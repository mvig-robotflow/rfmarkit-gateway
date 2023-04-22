import logging
import multiprocessing as mp
import os
import os.path as osp
import signal
import threading
import time
from typing import List, Optional, Dict, Union

import uvicorn
from fastapi import FastAPI
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse, RedirectResponse

from markit_gateway.common import IMUConnection, tcp_broadcast_command
from markit_gateway.config import BrokerConfig
from markit_gateway.functional import convert_measurement
from markit_gateway.tasks import measure
from markit_gateway.utils import get_datetime_tag, parse_cidr_addresses

app = FastAPI()
LOGGER: Optional[logging.Logger] = None

STOP_EV: mp.Event = mp.Event()
FINISH_EV: mp.Event = mp.Event()

# Values are reset from one run to another
TCP_PROCS: List[mp.Process] = []
IMU_STATES: Dict[str, Dict[str, Union[float, str, int]]] = {}  # index is device_id
IMU_ADDRESSES: Dict[str, Union[str, List[str]]] = {"unknown": []}  # index is device_id

CONFIG: Optional[BrokerConfig] = None
CLIENT_INFO_QUEUE: Optional[mp.Queue] = None
IMU_STATE_QUEUE: Optional[mp.Queue] = None


def make_response(status_code, **kwargs):
    data = {'code': status_code, 'timestamp': time.time()}
    data.update(**kwargs)
    json_compatible_data = jsonable_encoder(data)
    resp = JSONResponse(content=json_compatible_data, status_code=status_code)
    return resp


def measure_and_convert(
        cfg: BrokerConfig,
        tag: str,
        signal_stop: mp.Event = None,
        signal_finish: mp.Event = None,
        client_info_queue: mp.Queue = None,
        imu_state_queue: mp.Queue = None
):
    measure(cfg, tag, signal_stop, client_info_queue, imu_state_queue)

    try:
        convert_measurement(osp.join(cfg.base_dir, tag))
    except Exception as e:
        logging.error(e)

    signal_finish.set()


@app.get("/")
def root():
    return RedirectResponse(url='/docs')


@app.get("/v1/status")
def status():
    return make_response(status_code=200, active_processes=[proc.is_alive() for proc in TCP_PROCS].count(True))


@app.get("/v1/imu/connection")
def imu_connection():
    global IMU_STATES, IMU_ADDRESSES
    return make_response(status_code=200, count=len(IMU_STATES.keys()), imu_ids=list(IMU_STATES.keys()), imu_addresses=IMU_ADDRESSES)


@app.post("/v1/imu/control")
def imu_control(command: str = None):
    global IMU_ADDRESSES, CONFIG
    if command is None:
        return make_response(status_code=400, message="command is required")
    else:
        imu_addresses = parse_cidr_addresses(CONFIG.imu_addresses)
        resp = tcp_broadcast_command(imu_addresses, CONFIG.imu_port, command)
        return make_response(status_code=200, count=len(resp), resp=resp)


@app.get("/v1/imu/state")
def imu_state():
    global IMU_STATES
    return make_response(status_code=200, imu_states=IMU_STATES, count=len(IMU_STATES.keys()))


@app.get("/v1/imu/state/{device_id}")
def imu_state_device_id(device_id: str = None):
    global IMU_STATES
    if device_id is None:
        return make_response(status_code=400, message="device_id is required")
    else:
        if device_id in IMU_STATES.keys():
            return make_response(status_code=200, imu_state=IMU_STATES[device_id])
        else:
            return make_response(status_code=500, message=f"device_id  is not connected")


@app.post("/v1/start")
def start_process(tag: str = None, experiment_log: str = None):
    global TCP_PROCS, STOP_EV, FINISH_EV, CONFIG, LOGGER, CLIENT_INFO_QUEUE, IMU_STATE_QUEUE, IMU_STATES, IMU_ADDRESSES

    # Wait until last capture ends
    if len(TCP_PROCS) > 0:
        if STOP_EV.is_set():
            FINISH_EV.wait(timeout=0.5)
            if FINISH_EV.is_set():
                [proc.join(timeout=3) for proc in TCP_PROCS]
                if any([proc.is_alive() for proc in TCP_PROCS]):
                    LOGGER.warning(" Join timeout")
                    [os.kill(proc.pid, signal.SIGTERM) for proc in TCP_PROCS if proc.is_alive()]
                # Clean up memory, prepare for next run
                TCP_PROCS = []
                IMU_STATES = {}
                IMU_ADDRESSES = {"unknown": []}
            else:
                return make_response(status_code=500, msg="NOT FINISHED")
        else:
            return make_response(status_code=500, msg="RUNNING")

    if len(TCP_PROCS) == 0:
        STOP_EV.clear()
        FINISH_EV.clear()

        # Get measurement name
        if tag is None:
            tag = 'imu_mem_' + get_datetime_tag()
        LOGGER.info(f"tag={tag}")

        if experiment_log is None:
            experiment_log = 'None'
        LOGGER.info(f"experiment_log={experiment_log}")

        if len(TCP_PROCS) <= 0:
            TCP_PROCS = [
                mp.Process(
                    None,
                    measure_and_convert,
                    "measure_headless",
                    (
                        CONFIG,
                        tag,
                        STOP_EV,
                        FINISH_EV,
                        CLIENT_INFO_QUEUE,
                        IMU_STATE_QUEUE
                    )
                )
            ]
            [proc.start() for proc in TCP_PROCS]

        return make_response(status_code=200, msg="START OK", subpath=tag)


@app.post("/v1/stop")
def stop_process():
    global TCP_PROCS, STOP_EV, LOGGER
    LOGGER.info("stop")

    if len(TCP_PROCS) > 0 and any([proc.is_alive() for proc in TCP_PROCS]) > 0:
        STOP_EV.set()
        return make_response(status_code=200, msg=f"STOP OK: {len([None for proc in TCP_PROCS if proc.is_alive()])} procs are running")
    else:
        return make_response(status_code=500, msg="NOT RUNNING")


@app.post("/v1/kill")
def kill_record():
    global TCP_PROCS, STOP_EV, FINISH_EV, LOGGER
    LOGGER.info("killing processes")

    if len(TCP_PROCS) and any([proc.is_alive() for proc in TCP_PROCS]) > 0:
        STOP_EV.set()
        FINISH_EV.wait()
        [proc.join(timeout=4) for proc in TCP_PROCS]
        if any([proc.is_alive() for proc in TCP_PROCS]):
            LOGGER.warning("join timeout, force kill all processes")
            [os.kill(proc.pid, signal.SIGTERM) for proc in TCP_PROCS if proc.is_alive()]
        TCP_PROCS = []
        return make_response(status_code=200, msg="KILL OK")
    else:
        return make_response(status_code=500, msg="NOT RUNNING")


def update_imu_state_thread():
    global IMU_STATE_QUEUE, IMU_STATES, LOGGER
    while True:
        if IMU_STATE_QUEUE is not None:
            if not IMU_STATE_QUEUE.empty():
                try:
                    msg = IMU_STATE_QUEUE.get(timeout=0.1)
                    if msg is not None:
                        if msg['id'] in IMU_STATES.keys():
                            IMU_STATES[msg['id']] = msg
                except Exception:
                    pass
        else:
            time.sleep(0.1)


def update_client_info_thread():
    global CLIENT_INFO_QUEUE, IMU_STATES, LOGGER
    while True:
        if CLIENT_INFO_QUEUE is not None:
            if not CLIENT_INFO_QUEUE.empty():
                try:
                    conn: IMUConnection = CLIENT_INFO_QUEUE.get(timeout=0.1)
                    if conn is not None:
                        IMU_ADDRESSES['unknown'].append(conn.addr)
                        retry = 5
                        while conn.query_device_id() is None and retry > 0:
                            time.sleep(2)
                            retry -= 1

                        if retry > 0:
                            LOGGER.info(f"IMUConnection(addr={conn.addr}, device_id={conn.device_id})")
                            if conn.device_id not in IMU_STATES.keys():
                                IMU_STATES[conn.device_id] = {}
                            if conn.device_id not in IMU_ADDRESSES.keys():
                                IMU_ADDRESSES[conn.device_id] = conn.addr
                        else:
                            LOGGER.warning(f"failed to get device_id from IMUConnection(addr={conn.addr}, device_id=None)")
                except Exception:
                    pass
        else:
            time.sleep(0.1)


def portal(cfg: BrokerConfig):
    # Recording parameters
    global CONFIG, LOGGER, IMU_STATE_QUEUE, CLIENT_INFO_QUEUE

    IMU_STATE_QUEUE = mp.Queue()
    CLIENT_INFO_QUEUE = mp.Queue()

    CONFIG = cfg

    # setting global parameters
    logging.basicConfig(level=logging.INFO)
    LOGGER = logging.getLogger("markit_gateway.portal")
    # Prepare system
    LOGGER.info(f"prepare markit_gateway:{cfg.imu_port} at {cfg.api_port}")

    # Start threads
    threading.Thread(target=update_imu_state_thread, daemon=True).start()
    threading.Thread(target=update_client_info_thread, daemon=True).start()

    try:
        # app.run(host='0.0.0.0', port=api_port)
        uvicorn.run(app=app, port=cfg.api_port, host='0.0.0.0')
    except KeyboardInterrupt:
        LOGGER.info(f"portal() got KeyboardInterrupt")
        return


if __name__ == '__main__':
    portal(BrokerConfig('./imu_config.yaml'))
