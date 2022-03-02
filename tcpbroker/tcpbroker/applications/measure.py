import logging
import multiprocessing as mp
import os

from tcpbroker.config import BrokerConfig
from tcpbroker.tasks import tcp_listen_task
from .control import control


def measure(port: int, config: BrokerConfig, measurement_name: str, with_control: bool = True):
    # Listen TCP
    client_addr_queue = mp.Queue()

    stop_ev = mp.Event()
    finish_ev = mp.Event()

    tcp_listen_task_process = mp.Process(None, tcp_listen_task, "tcp_listen_task",
                                         ('0.0.0.0', port, config, measurement_name, stop_ev, finish_ev, client_addr_queue,))
    tcp_listen_task_process.start()

    if with_control:
        control(port, config, client_addr_queue)
    else:
        while True:
            try:
                cmd = input("> ")
                if cmd in ["quit", "q"]:
                    break
            except KeyboardInterrupt:
                break
    stop_ev.set()

    # try:
    #     os.kill(tcp_listen_task_process.pid, signal.SIGTERM)
    #     print("Joining listen tasks")
    #     tcp_listen_task_process.join()
    # except KeyboardInterrupt:
    #     time.sleep(0.1)
    #     os.kill(tcp_listen_task_process.pid, signal.SIGTERM)
    #     tcp_listen_task_process.join()

    finish_ev.wait()

    # Write readme
    measurement_basedir = os.path.join(config.DATA_DIR, measurement_name)
    experiment_logs = input("Experiment logs:\n> ")
    logging.info(f"Writting README")
    with open(os.path.join(measurement_basedir, 'README'), 'w') as f:
        f.write(measurement_name + '\n')
        f.write(experiment_logs + '\n')
