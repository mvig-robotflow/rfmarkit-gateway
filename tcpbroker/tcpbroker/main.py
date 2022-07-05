import argparse
import logging
import os
from datetime import datetime

from cvt_measurement import convert_measurement
from tcpbroker.applications import measure, control, test, portal


def print_help():
    print("\
 Usage: \n\
    > start [measurement_name] - start measurement\n\
    > control - begin control program\n\
    > test    - begin test program\n\
    > portal  - enter portal mode\n\
    > quit    - quit program\n")


def main(args):
    from tcpbroker.config import BrokerConfig
    config = BrokerConfig(args.config)

    logging.basicConfig(level=logging.DEBUG) if config.DEBUG else logging.basicConfig(level=logging.INFO)

    print("Welcome to Inertial Measurement Unit Data collecting system \n\n")
    print_help()
    port = args.port
    if args.P:
        portal(port, config, config.API_PORT)
        exit(0)

    while True:
        try:
            cmd = input("> ").split(' ')
        except KeyboardInterrupt:
            logging.info("Exiting")
            return

        if cmd[0] in ['start', 's']:

            if len(cmd) > 1:
                measurement_name = cmd[1]
            else:
                measurement_name = 'imu_mem_' + datetime.now().strftime("%Y-%m-%d_%H%M%S")
            print(f"Starting measurement: {measurement_name}, enter quit/q to stop")
            measure(port, config, measurement_name, False)
            # Convert
            try:
                convert_measurement(os.path.join(config.DATA_DIR, measurement_name))
            except Exception as e:
                logging.warning(e)

        elif cmd[0] in ['control', 'c']:
            control(port, config)
            print(f"Starting control app")

        elif cmd[0] in ['test', 't']:
            test('0.0.0.0', port)
        elif cmd[0] in ['portal', 'p']:
            portal(port, config, config.API_PORT)

        elif cmd[0] in ['quit', 'q', 'exit']:
            print(f"Exiting....")
            exit(0)

        else:
            print(f"Invalid command: {' '.join(cmd)}")

        print_help()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int, default=18888)
    parser.add_argument('-P', action="store_true")
    parser.add_argument('--config', type=str, default='./config.json')
    args = parser.parse_args()

    main(args)
