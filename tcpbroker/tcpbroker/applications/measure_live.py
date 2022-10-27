import logging
import multiprocessing as mp
import os

from tcpbroker.config import BrokerConfig
from tcpbroker.tasks import tcp_listen_live_task, imu_render_ui_task
from .control import control


def measure_live(port: int, config: BrokerConfig, measurement_name: str, with_control: bool = True):
    # Listen TCP
    client_addr_queue = mp.Queue()

    stop_ev = {
        'tcp': mp.Event(),
        'ui': mp.Event()
    }
    finish_ev = {
        'tcp': mp.Event(),
        'ui': mp.Event()
    }

    imu_stat_queue = mp.Queue()

    tcp_listen_task_process = mp.Process(None, tcp_listen_live_task, "tcp_listen_live_task",
                                         ('0.0.0.0', port, config, measurement_name, stop_ev['tcp'], finish_ev['tcp'],
                                          client_addr_queue, imu_stat_queue))
    tcp_listen_task_process.start()

    imu_render_task_process = mp.Process(None, imu_render_ui_task, "imu_render_ui_task",
                                         (stop_ev['ui'], finish_ev['ui'], imu_stat_queue,))
    imu_render_task_process.start()

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

    for ev in stop_ev.values():
        ev.set()
    for ev in finish_ev.values():
        ev.wait()

    # Write readme
    measurement_basedir = os.path.join(config.DATA_DIR, measurement_name)
    experiment_logs = input("Experiment logs:\n> ")
    logging.info(f"Writting README")
    with open(os.path.join(measurement_basedir, 'README'), 'w') as f:
        f.write(measurement_name + '\n')
        f.write(experiment_logs + '\n')
