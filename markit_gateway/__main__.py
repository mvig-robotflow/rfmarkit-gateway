import argparse
import sys

from markit_gateway.scripts import cli, configure
from markit_gateway.cmd import portal
from .config import BrokerConfig

if __name__ == '__main__':
    argv = sys.argv[1:]
    if len(argv) > 0:
        if sys.argv[0] == 'configure':
            parser = argparse.ArgumentParser()
            parser.add_argument("--input", "-i", type=str, default=None, help="path to input config file")
            parser.add_argument("--output", "-o", type=str, default="imu_config.yaml", help="path to output config file")
            args = parser.parse_args(sys.argv[2:])
            configure(args)
        elif argv[0] == 'serve':
            parser = argparse.ArgumentParser()
            parser.add_argument('--config', type=str, default='./imu_config.yaml', help="path to config file")
            args = parser.parse_args(argv[1:])
            option = BrokerConfig(args.config)
            portal(option)

    else:
        parser = argparse.ArgumentParser()
        parser.add_argument('-P', action="store_true", help="portal mode")
        parser.add_argument('--easy', action="store_true", help="start easy setup")
        parser.add_argument('--config', type=str, default='./imu_config.yaml', help="path to config file")
        args = parser.parse_args()
        cli(args)
