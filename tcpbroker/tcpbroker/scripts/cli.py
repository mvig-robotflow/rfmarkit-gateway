import argparse
import cmd
import logging
import multiprocessing as mp
import os.path
import os.path as osp
import signal
from datetime import datetime
from typing import Optional

from rich.console import Console

from cvt_measurement import convert_measurement
from tcpbroker.cmd import control_from_keyboard, portal, easy_setup
from tcpbroker.config import BrokerConfig
from tcpbroker.tasks import measure

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
        p = mp.Process(None,
                       measure,
                       "measure",
                       (
                           tmp_option,
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

        # Delete tmp file
        os.removedirs(osp.join(self.option.base_dir, tag))

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

        logger = logging.getLogger('tcpbroker')
        logger.setLevel(logging.DEBUG) if option.debug else logger.setLevel(logging.INFO)

        if args.P:
            portal(option)
            exit(0)
        elif args.easy:
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
