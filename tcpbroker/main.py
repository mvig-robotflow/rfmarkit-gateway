import argparse
import logging
from datetime import datetime

from config import DEBUG

logging.basicConfig(level=logging.DEBUG) if DEBUG else logging.basicConfig(level=logging.INFO)

from applications import measure, control, test


def print_help():
    print("\
 Usage: \n\
    > start [measurement_name] - start measurement\n\
    > control - begin control program\n\
    > test    - begin test program\n\
    > quit    - quit program\n")


def main(PORT: int):
    print("Welcome to Inertial Measurement Unit Data collecting system \n\n")
    print_help()
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
            print(f"Starting measurement: {measurement_name}")
            measure(PORT, measurement_name)

        elif cmd[0] in ['control', 'c']:
            control(PORT)
            print(f"Starting control app")

        elif cmd[0] in ['test', 't']:
            test('0.0.0.0', PORT)

        elif cmd[0] in ['quit', 'q', 'exit']:
            print(f"Exiting...")
            return

        else:
            print(f"Invalid command: {' '.join(cmd)}")

        print_help()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int, default=18888)
    args = parser.parse_args()

    main(args.port)
