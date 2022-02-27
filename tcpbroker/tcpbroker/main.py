import argparse
import logging
import os
from datetime import datetime

from config import DEBUG, DATA_DIR, API_PORT
from cvt_measurement import convert_measurement

logging.basicConfig(level=logging.DEBUG) if DEBUG else logging.basicConfig(level=logging.INFO)

from applications import measure, control, test, portal


def print_help():
    print("\
 Usage: \n\
    > start [measurement_name] - start measurement\n\
    > control - begin control program\n\
    > test    - begin test program\n\
    > portal  - enter portal mode\n\
    > quit    - quit program\n")


def main(args):
    print("Welcome to Inertial Measurement Unit Data collecting system \n\n")
    print_help()
    port = args.port
    if args.p:
        portal(port, API_PORT)
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
            measure(port, measurement_name, False)
            # Convert
            try:
                convert_measurement(os.path.join(DATA_DIR, measurement_name))
            except Exception as e:
                logging.warning(e)
                raise e

        elif cmd[0] in ['control', 'c']:
            control(port)
            print(f"Starting control app")

        elif cmd[0] in ['test', 't']:
            test('0.0.0.0', port)
        elif cmd[0] in ['portal', 'p']:
            portal(port, API_PORT)

        elif cmd[0] in ['quit', 'q', 'exit']:
            print(f"Exiting....")
            exit(0)

        else:
            print(f"Invalid command: {' '.join(cmd)}")

        print_help()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int, default=18888)
    parser.add_argument('-p', action="store_true")
    args = parser.parse_args()

    main(args)
