import json
import logging
import multiprocessing as mp
import os
import signal
import sys
import time
from datetime import datetime
from typing import List

from flask import Flask, request, Response
from tasks import tcp_listen_task
from gevent import pywsgi
from cvt_measurement import convert_measurement

app = Flask(__name__)

STOP_EV: mp.Event = mp.Event()
FINISH_EV: mp.Event = mp.Event()
TCP_PROCS: List[mp.Process] = []
PORT: int = 0


def make_response(status, msg="", **kwargs):
    data = {'status': status, 'msg': msg, 'timestamp': time.time()}
    data.update(**kwargs)
    resp = Response(mimetype='application/json', status=200)
    resp.data = json.dumps(data)
    return resp


from config import DATA_DIR


def measure_headless(measure_stop_ev: mp.Event(),
                     measure_finish_ev: mp.Event(),
                     port: int,
                     measurement_name: str,
                     experiment_log: str):
    stop_ev = mp.Event()
    finish_ev = mp.Event()

    # Listen TCP
    client_addr_queue = mp.Queue(maxsize=32)

    tcp_listen_task_process = mp.Process(None, tcp_listen_task, "tcp_listen_task",
                                         ('0.0.0.0', port, measurement_name, stop_ev, finish_ev, client_addr_queue,))
    tcp_listen_task_process.start()

    measure_stop_ev.wait()
    stop_ev.set()
    finish_ev.wait()

    # Write readme
    measurement_basedir = os.path.join(DATA_DIR, measurement_name)
    logging.info(f"[tcpbroker] Writting README to {measurement_basedir}")

    with open(os.path.join(measurement_basedir, 'README'), 'w') as f:
        f.write(measurement_name + '\n')
        f.write(experiment_log + '\n')

    # Convert
    try:
        convert_measurement(os.path.join(DATA_DIR, measurement_name))
    except Exception as e:
        logging.warning(e)
        raise e

    measure_finish_ev.set()


@app.route("/", methods=['POST', 'GET'])
def index():
    return make_response(status=200, msg=f"ActiveProcesses={len([None for proc in TCP_PROCS if proc.is_alive()])}")


@app.route("/start", methods=['POST', 'GET'])
def start_record():
    global TCP_PROCS, STOP_EV, FINISH_EV, SAVE_PATH_BASE, PORT

    # Wait until last capture ends
    if len(TCP_PROCS) > 0:
        if STOP_EV.is_set():
            FINISH_EV.wait(timeout=0.5)
            if FINISH_EV.is_set():
                [proc.join(timeout=3) for proc in TCP_PROCS]
                if any([proc.is_alive() for proc in TCP_PROCS]):
                    logging.warning("[Solocam] Join timeout")
                    [os.kill(proc.pid, signal.SIGTERM) for proc in TCP_PROCS if proc.is_alive()]
                TCP_PROCS = []
            else:
                return make_response(status=500, msg="NOT FINISHED")
        else:
            return make_response(status=500, msg="RUNNING")

    if len(TCP_PROCS) == 0:
        STOP_EV.clear()
        FINISH_EV.clear()

        # Get measurement name
        try:
            measurement_name = request.get_json()["measurement_name"]  # extract measurement name
            logging.info(f"[tcpbroker] measurement_name={measurement_name}")
        except Exception:
            measurement_name = measurement_name = 'imu_mem_' + datetime.now().strftime("%Y-%m-%d_%H%M%S")

        try:
            experiment_log = request.get_json()["experiment_log"]  # extract log
            logging.info(f"[tcpbroker] experiment_log={experiment_log}")
        except Exception:
            experiment_log = 'None'

        if len(TCP_PROCS) <= 0:
            TCP_PROCS = [mp.Process(None, measure_headless, "measure_headless", (STOP_EV,
                                                                                 FINISH_EV,
                                                                                 PORT,
                                                                                 measurement_name,
                                                                                 experiment_log,))]
            [proc.start() for proc in TCP_PROCS]

        return make_response(status=200, msg=f"START OK, subpath={measurement_name}")


@app.route("/stop", methods=['POST', 'GET'])
def stop_record():
    global TCP_PROCS, STOP_EV
    logging.info("[tcpbroker] Stop")

    if len(TCP_PROCS) > 0:
        STOP_EV.set()
        return make_response(status=200, msg=f"STOP OK: {len([None for proc in TCP_PROCS if proc.is_alive()])} procs are running")
    else:
        return make_response(status=500, msg="NOT RUNNING")


@app.route("/kill", methods=['POST', 'GET'])
def kill_record():
    global TCP_PROCS, STOP_EV, FINISH_EV
    logging.info("[tcpbroker] kill")

    if len(TCP_PROCS) > 0:
        STOP_EV.set()
        FINISH_EV.wait()
        [proc.join(timeout=3) for proc in TCP_PROCS]
        if any([proc.is_alive() for proc in TCP_PROCS]):
            logging.warning("[tcpbroker] Join timeout")
            [os.kill(proc.pid, signal.SIGTERM) for proc in TCP_PROCS if proc.is_alive()]
        TCP_PROCS = []
        return make_response(status=200, msg="KILL OK")
    else:
        return make_response(status=500, msg="NOT RUNNING")


@app.route("/quit", methods=['POST', 'GET'])
def quit():
    global TCP_PROCS, STOP_EV, FINISH_EV
    logging.info("[tcpbroker] quit")

    if len(TCP_PROCS) > 0:
        kill_record()
        sys.exit(1)
    else:
        sys.exit(0)


def portal(port: int):
    # Recording parameters
    global SAVE_PATH_BASE, CAMERA_INFO, CAMERA_GROUP, PORT

    SAVE_PATH_BASE = "C:\\Users\\liyutong\\Data\\imu-highspeed-cam"

    PORT = port

    # setting global parameters
    logging.basicConfig(level=logging.INFO)
    # Prepare system
    logging.info(f"[tcpbroker] Prepare tcpbroker:{PORT}")

    try:
        # app.run(host='0.0.0.0', port=5050)
        server = pywsgi.WSGIServer(('0.0.0.0', 5050), app)
        server.serve_forever()
    except KeyboardInterrupt:
        print(f"[tcpbroker]:  Main got KeyboardInterrupt")
        return


if __name__ == '__main__':
    portal(18888)
