import argparse
import logging
import asyncio

from datetime import datetime
from config import DEBUG

logging.basicConfig(level=logging.DEBUG) if DEBUG else logging.basicConfig(level=logging.INFO)

from tasks import tcp_listen_task
from applications import measure, control

def main(PORT):
    print("Welcome to Inertial Measurement Unit Data collecting system \n\n Usage: \n    > start [measurement_name]    - start measurement\n    > control    - begin control program\n    > quit    - quit program")
    while True:
        cmd = input("> ").split(' ')
        
        if cmd[0] in ['start', 's', '']:

            if len(cmd) > 1:
                measurement_name = cmd[1]
            else:
                measurement_name = 'imu_mem_' + datetime.now().strftime("%Y-%m-%d_%H%M%S")
            print(f"Starting measurement: {measurement_name}")
            measure(PORT, measurement_name)

        elif cmd[0] in ['control', 'c']:
            asyncio.run(control(PORT))
            print(f"Starting control app")
        
        elif cmd[0] in ['quit', 'q', 'exit']:
            print(f"Exitting...")
            return

        else:
            print(f"Invalid command: {' '.join(cmd)}")
        
        print("Usage: \n    > start [measurement_name]    - start measurement\n    > control    - begin control program\n    > quit    - quit program")

if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int, default=18888)
    args = parser.parse_args()
    
    main(args.port)
