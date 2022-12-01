import argparse
import cmd
import logging
import multiprocessing as mp
import os.path as osp
from datetime import datetime
from typing import Optional

from rich.console import Console

from cvt_measurement import convert_measurement
from tcpbroker.applications import control_from_keyboard, portal, easy_setup
from tcpbroker.config import BrokerConfig
from tcpbroker.tasks import measure


def print_help():
    print("\
 Usage: \n\
    > start [measurement_name] - start measurement\n\
    > easy_setup - begin easy_setup program\n\
    > control - begin control program\n\
    > portal  - enter portal mode\n\
    > quit    - quit program\n")


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
        p.join()

        # Convert
        try:
            convert_measurement(osp.join(self.option.base_dir, tag))
        except Exception as e:
            self.console.log(e, style="red")

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
    config = BrokerConfig(args.config)
    logging.basicConfig(level=logging.DEBUG) if config.debug else logging.basicConfig(level=logging.INFO)

    logger = logging.getLogger('tcpbroker')
    logger.setLevel(logging.DEBUG) if config.debug else logger.setLevel(logging.INFO)

    if args.P:
        portal(config)
        exit(0)
    elif args.easy:
        easy_setup(config)
        exit(0)
    else:
        IMUConsole(config).cmdloop()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-P', action="store_true")
    parser.add_argument('--easy', action="store_true")
    parser.add_argument('--config', type=str, default='./imu_config.yaml')
    args = parser.parse_args()

    main(args)
