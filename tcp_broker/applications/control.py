import socket
from concurrent.futures import ThreadPoolExecutor
import logging
import time

logging.basicConfig(level=logging.INFO)

from typing import List


def hold(subnet, port):
    try:
        while True:
            logging.warn("Holding")
            with ThreadPoolExecutor(64) as executor:
                for ret in executor.map(tcp_send_bytes, gen_arguments(subnet, port, 'ping')):
                    if len(ret['msg']) > 0:
                        print(f"{(ret['addr'])} return: {ret['msg']}")
            time.sleep(30)
    except KeyboardInterrupt as err:
        return



def tcp_send_bytes(arguments):
    addr: str = arguments['addr']
    port: int = arguments['port']
    data: int = arguments['data']
    reply = ''

    logging.debug(f"Sending {data} to {addr}:{port}")

    # Setup the server
    ctrl_socket: socket.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # ctrl_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    ctrl_socket.settimeout(2)  # TODO: Magic timeout
    try:
        ctrl_socket.connect((addr, port))
    except Exception as err:
        if isinstance(err, socket.timeout) or isinstance(err, ConnectionRefusedError):
            return {"addr": addr, "msg": reply}
        else:
            logging.warning(f"{err} for {addr}")
            return {"addr": addr, "msg": reply}

    ctrl_socket.settimeout(10)  # TODO: Magic timeout

    try:
        ctrl_socket.send(data)
        while True:
            reply += str(ctrl_socket.recv(1024), encoding='ascii')
    except socket.timeout:
        logging.warning(f"Socket timeout for {addr}")
    return {"addr": addr, "msg": reply}


def gen_arguments(subnet: List[int], port: int, command: str):  # TODO: Only support *.*.*.0/24
    postfix = subnet[-1]
    data = bytes(command, encoding='ascii')
    while postfix < 256:
        yield {'addr': ".".join(map(lambda x: str(x), subnet[:3])) + '.' + str(postfix), 'port': port, 'data': data}
        postfix += 1


def control(port: int):
    # Get subnet, like [10,52,24,0]
    try:
        subnet: List[int] = list(map(lambda x: int(x), input("Input subnet of IMUs, e.g. 10.52.24.0\n> ").split(".")))
    except ValueError:
        logging.info("Wrong input, use default value(10.52.24.0)")
        subnet = [10, 52, 24, 0]

    print(
        f"Welcome to Inertial Measurement Unit control system \n\nSending to {subnet}\nCommands: \n    > restart\n    > ping\n    > sleep\n    > shutdown\n    > update\n    > cali_reset\n    > cali_acc\n    > cali_mag\n    > start\n    > stop\n\n    > quit - quit this tool\n"
    )
    n_repeat: int = 1
    try:
        while True:
            command = input("> ")
            if command in ['quit', 'q']:
                break
            elif command in ['hold', 'h']:
                hold(subnet, port)
                continue

            with ThreadPoolExecutor(64) as executor:
                for ret in executor.map(tcp_send_bytes, gen_arguments(subnet, port, command)):
                    if len(ret['msg']) > 0:
                        print(f"{(ret['addr'])} return: {ret['msg']}")

            print(
                "\nCommands: \n    > restart\n    > ping\n    > sleep\n    > shutdown\n    > update\n    > cali_reset\n    > cali_acc\n    > cali_mag\n    > start\n    > stop\n\n    > quit - quit this tool\n"
            )
    except KeyboardInterrupt:
        print("Exitting")
        return


if __name__ == '__main__':
    control(18888)
