import logging
import multiprocessing as mp
import os
import os.path as osp
import signal
import time
from typing import List, Optional

import uvicorn
from fastapi import FastAPI
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse, RedirectResponse

from cvt_measurement import convert_measurement
from tcpbroker.config import BrokerConfig
from tcpbroker.tasks import measure
from tcpbroker.utils import get_datetime_tag

app = FastAPI()

STOP_EV: mp.Event = mp.Event()
FINISH_EV: mp.Event = mp.Event()
TCP_PROCS: List[mp.Process] = []
CONFIG: Optional[BrokerConfig] = None
LOGGER: Optional[logging.Logger] = None


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
        imu_stat_queue: mp.Queue = None
):
    global LOGGER
    measure(cfg, tag, signal_stop, client_info_queue, imu_stat_queue)

    try:
        convert_measurement(osp.join(cfg.base_dir, tag))
    except Exception as e:
        LOGGER.error(e)

    signal_finish.set()


@app.get("/")
def root():
    return RedirectResponse(url='/docs')


@app.get("/v1/status")
def status():
    return make_response(status_code=200, active_processes=[proc.is_alive() for proc in TCP_PROCS].count(True))


@app.post("/v1/start")
def start_process(tag: str = None, experiment_log: str = None):
    global TCP_PROCS, STOP_EV, FINISH_EV, CONFIG, LOGGER

    # Wait until last capture ends
    if len(TCP_PROCS) > 0:
        if STOP_EV.is_set():
            FINISH_EV.wait(timeout=0.5)
            if FINISH_EV.is_set():
                [proc.join(timeout=3) for proc in TCP_PROCS]
                if any([proc.is_alive() for proc in TCP_PROCS]):
                    LOGGER.warning(" Join timeout")
                    [os.kill(proc.pid, signal.SIGTERM) for proc in TCP_PROCS if proc.is_alive()]
                TCP_PROCS = []
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

        client_info_queue = mp.Queue()
        imu_stat_queue = mp.Queue()

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
                        client_info_queue,
                        imu_stat_queue
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


def portal(cfg: BrokerConfig):
    # Recording parameters
    global IMU_PORT, CONFIG, LOGGER

    IMU_PORT = cfg.imu_port
    API_PORT = cfg.api_port
    CONFIG = cfg

    # setting global parameters
    logging.basicConfig(level=logging.INFO)
    LOGGER = logging.getLogger("tcpbroker.portal")
    # Prepare system
    LOGGER.info(f"prepare tcpbroker:{IMU_PORT} at {API_PORT}")

    try:
        # app.run(host='0.0.0.0', port=api_port)
        uvicorn.run(app=app, port=API_PORT)
    except KeyboardInterrupt:
        LOGGER.info(f"portal() got KeyboardInterrupt")
        return


if __name__ == '__main__':
    portal(BrokerConfig('./imu_config.yaml'))
