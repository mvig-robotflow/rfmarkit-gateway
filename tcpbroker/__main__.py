import argparse
import sys

from .scripts import cli, configure

if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == 'configure':
        parser = argparse.ArgumentParser()
        parser.add_argument("--input", "-i", type=str, default=None, help="path to input config file")
        parser.add_argument("--output", "-o", type=str, default="imu_config.yaml", help="path to output config file")
        args = parser.parse_args(sys.argv[2:])
        configure(args)
    else:
        parser = argparse.ArgumentParser()
        parser.add_argument('-P', action="store_true", help="portal mode")
        parser.add_argument('--easy', action="store_true", help="start easy setup")
        parser.add_argument('--config', type=str, default='./imu_config.yaml', help="path to config file")
        args = parser.parse_args()
        cli(args)
