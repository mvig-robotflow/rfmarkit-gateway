import argparse
import logging
import multiprocessing as mp
import os.path
import os.path as osp
import shutil
import signal
import threading
import time
from datetime import datetime
from typing import Optional

from rich.console import Console

import cmd
from markit_gateway.cmd import control_from_keyboard, portal, easy_setup
from markit_gateway.common import IMUConnection
from markit_gateway.config import BrokerConfig
from markit_gateway.functional import convert_measurement
from markit_gateway.tasks import measure


class IMUConsole(cmd.Cmd):
    intro = "Welcome to the Inertial Measurement Unit Data collecting system.   Type help or ? to list commands.\n"
    prompt = "(imu) "

    option: Optional[BrokerConfig] = None

    def __init__(self, option: BrokerConfig):
        super().__init__()
        self.console = Console()
        self.option = option
        self.console.log(f"using {self.option.base_dir} as storage backend")
        self.measurement_name = None

    def do_start(self, arg):
        """start [measurement_name] - start measurement"""
        tag: str
        if len(arg) > 1:
            tag = str(arg.split()[0])
        else:
            tag = 'imu_mem_' + datetime.now().strftime("%Y-%m-%d_%H%M%S")
        self.console.print(f"Starting measurement, tag={tag}")

        signal_stop = mp.Event()
        signal_stop.clear()
        p = mp.Process(None,
                       measure,
                       "measure",
                       (
                           self.option,
                           tag,
                           signal_stop,
                       ), daemon=False)
        p.start()
        try:
            self.console.input("Press \\[enter] to stop measurement \n")
        except KeyboardInterrupt:
            pass

        signal_stop.set()
        p.join(timeout=20)
        if p.is_alive():
            os.kill(p.pid, signal.SIGTERM)

        # Convert
        try:
            convert_measurement(osp.join(self.option.base_dir, tag))
        except Exception as e:
            self.console.log(e, style="red")

    def do_calibrate(self, arg):
        """calibrate - calibrate imu"""
        tag = "_tmp"

        signal_stop = mp.Event()
        signal_stop.clear()
        tmp_option = self.option
        tmp_option.enable_gui = True
        client_info_queue = mp.Queue()
        p = mp.Process(None,
                       measure,
                       "measure",
                       (
                           tmp_option,
                           tag,
                           signal_stop,
                           client_info_queue
                       ), daemon=False)
        p.start()

        def trigger_imu(q: mp.Queue):
            while True:
                if not q.empty():
                    try:
                        conn: IMUConnection = q.get(timeout=0.1)
                        if conn is not None:
                            retry = 5
                            while retry > 0:
                                time.sleep(2)
                                ret = conn.start()
                                if ret is not None:
                                    break
                                retry -= 1

                                self.console.log(f"failed to trigger IMUConnection(addr={conn.addr}, device_id=None)")
                        else:
                            self.console.log("IMUConnection is None, stopping trigger")
                            break
                    except Exception:
                        break
                else:
                    time.sleep(0.1)

        trigger = threading.Thread(target=trigger_imu, args=(client_info_queue,))
        trigger.start()

        try:
            self.console.input("Press \\[enter] to stop calibration \n")
        except KeyboardInterrupt:
            pass

        signal_stop.set()
        client_info_queue.put(None)
        trigger.join(timeout=5)
        p.join(timeout=5)
        if p.is_alive():
            self.console.log("calibration process is still alive, killing it")
            os.kill(p.pid, signal.SIGTERM)
            if p.is_alive():
                self.console.log("failed to kill calibration process, please kill it manually")
        if trigger.is_alive():
            self.console.log("trigger thread is still alive")

        # Delete tmp file
        shutil.rmtree(osp.join(self.option.base_dir, tag))

    def do_control(self, arg):
        """control - begin control program"""
        control_from_keyboard(self.option)

    def do_easy_setup(self, arg):
        """easy_setup - begin easy_setup program"""
        easy_setup(self.option)

    def do_portal(self, arg):
        """portal - enter portal mode"""
        portal(self.option)

    def do_quit(self, arg):
        """exit - exit program"""
        self.console.log("Thank you, bye!")
        exit(0)


def main(args):
    if os.path.exists(args.config):
        option = BrokerConfig(args.config)

        logging.basicConfig(level=logging.DEBUG) if option.debug else logging.basicConfig(level=logging.INFO)

        logger = logging.getLogger('markit_gateway')
        logger.setLevel(logging.DEBUG) if option.debug else logger.setLevel(logging.INFO)

        if hasattr(args, 'P') and args.P:
            portal(option)
            exit(0)
        elif hasattr(args, 'easy') and args.easy:
            easy_setup(option)
            exit(0)
        else:
            IMUConsole(option).cmdloop()
    else:
        logging.error(f"Config file {args.config} not found")
        exit(1)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-P', action="store_true", help="portal mode")
    parser.add_argument('--easy', action="store_true", help="start easy setup")
    parser.add_argument('--config', type=str, default='./imu_config.yaml', help="path to config file")

    args = parser.parse_args()

    main(args)
