import logging
import multiprocessing as mp
import socket
from concurrent.futures import ThreadPoolExecutor
from typing import List, Union

from tcpbroker.config import BrokerConfig
from tcpbroker.applications.control import probe, broadcast_command

def print_help():
    print("\n\
    > 1. 查看在线传感器情况\n\
    > 2. 启动传感器\n\
    > 3. 停止传感器\n\
    > 4. 重置传感器\n\
    \n\n")


def easy_setup(port: int, config: BrokerConfig, client_queue: mp.Queue = None):
    # Get subnet, like [10,52,24,0]
    subnet = list(map(lambda x: int(x), config.DEFAULT_SUBNET.split("."))) if config.DEFAULT_SUBNET is not None else None
    if subnet is None:
        try:
            subnet: List[int] = list(
                map(lambda x: int(x), input("输入IMU网段，将被认为是/24网段, e.g. 10.53.24.0\n> ").split(".")))
        except ValueError:
            logging.info("Wrong input, use default value(192.168.1.0)")
            subnet = [192, 168, 1, 0]

        except (KeyboardInterrupt, EOFError):
            print("Control Exiting")
            return

    if client_queue is not None:
        client_addrs: Union[None, set] = set([])
    else:
        client_addrs = None

    print(f"欢迎使用IMU控制系统，\n\n 发送到{subnet}\n")

    try:
        while True:
            print_help()
            command = input("> ")
            try:
                command = int(command)
            except ValueError:
                print("\n错误的输入\n")
                continue
            
            if command == 1:
                broadcast_command(subnet, port, "ping", None)
            elif command == 2:
                broadcast_command(subnet, port, "start", None)
            elif command == 3:
                broadcast_command(subnet, port, "stop", None)
            elif command == 4:
                broadcast_command(subnet, port, "restart", None)
            else:
                print("\n错误的输入\n")

            # print_help()
    except (KeyboardInterrupt, EOFError):
        print("Control Exiting")
        return


if __name__ == '__main__':
    easy_setup(18888, BrokerConfig('./config.json'))
