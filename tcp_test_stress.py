import subprocess
import time
from typing import List
import argparse
import sys
import logging
logging.basicConfig(level=logging.INFO)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--world_sz', type=int, default=10)
    parser.add_argument('--name', type=str, default='tcp_test.py')

    args: argparse.Namespace = parser.parse_args()
    # - world_sz: int total number of clients

    process_list = []
    for id in range(args.world_sz):
        p = subprocess.Popen(f'{sys.executable} {args.name}', shell=True)
        process_list.append(p)
        time.sleep(0.5)
    
    logging.info(f"Processes: {process_list}")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        for p in process_list:
            try:
                p.kill()
                p.terminate()
            except:
                print(f"[ Error ] Unable to kill processes")
        raise KeyboardInterrupt