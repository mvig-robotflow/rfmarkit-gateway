import argparse

import yaml

from markit_gateway.config import BrokerConfig


def main(args: argparse.Namespace):
    if args.input is not None:
        with open(args.input) as f:
            base_cfg_dict = yaml.load(f, Loader=yaml.SafeLoader)
    else:
        base_cfg_dict = None

    cfg = BrokerConfig()
    cfg.configure_from_keyboard()

    cfg_dict = {'imu': cfg.get_dict() if base_cfg_dict is None else {**base_cfg_dict, **cfg.get_dict()}}  # type: ignore

    with open(args.output, 'w') as f:
        yaml.dump(cfg_dict, f)
    pass


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", "-i", type=str, default=None, help="path to input config file")
    parser.add_argument("--output", "-o", type=str, default="imu_config.yaml", help="path to output config file")
    args = parser.parse_args()
    main(args)
