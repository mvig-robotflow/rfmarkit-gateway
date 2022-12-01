import logging
import multiprocessing as mp
import time
import signal

from tcpbroker.config import BrokerConfig
from .imu_render_ui import imu_render_ui_task
from .tcp_listen import tcp_listen_task

_logger = logging.getLogger('measure')


def keyboard_interrupt_handler(signum, frame):
    print("KeyboardInterrupt (ID: {}) has been caught. Cleaning up...".format(signum))
    raise KeyboardInterrupt


def measure(config: BrokerConfig,
            tag: str,
            signal_stop: mp.Event = None,
            client_info_queue: mp.Queue = None,
            imu_stat_queue: mp.Queue = None):
    _logger.setLevel(logging.DEBUG) if config.debug else _logger.setLevel(logging.INFO)
    _logger.debug("start")
    # Listen TCP
    stop_ev = {
        'tcp': mp.Event(),
        'ui': mp.Event()
    }
    finish_ev = {
        'tcp': mp.Event(),
        'ui': mp.Event()
    }

    tcp_listen_task_process = mp.Process(None,
                                         tcp_listen_task,
                                         "tcp_listen_task",
                                         (
                                             config,
                                             tag,
                                             stop_ev['tcp'],
                                             finish_ev['tcp'],
                                             client_info_queue,
                                             imu_stat_queue
                                         ))
    _logger.debug("start tcp_listen_task")
    tcp_listen_task_process.start()

    if config.enable_gui:
        logging.debug("start imu_render_ui_task")
        imu_render_task_process = mp.Process(None,
                                             imu_render_ui_task,
                                             "imu_render_ui_task",
                                             (
                                                 stop_ev['ui'],
                                                 finish_ev['ui'],
                                                 imu_stat_queue
                                             ))
        imu_render_task_process.start()
    #
    # _logger.debug("configure signal handler")
    # signal.signal(signal.SIGINT, keyboard_interrupt_handler)
    while True:
        try:
            if signal_stop is not None:
                signal_stop.wait()
                break
            else:
                time.sleep(10)
        except KeyboardInterrupt:
            break

    _logger.debug("notify tcp_listen_task to stop")
    stop_ev['tcp'].set()
    _logger.debug("notify imu_render_ui_task to stop")
    stop_ev['ui'].set()
    # finish_ev['tcp'].wait()
    time.sleep(5)
    _logger.debug("measure stopped")
