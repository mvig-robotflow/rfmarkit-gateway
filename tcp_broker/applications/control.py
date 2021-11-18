import socket
from concurrent.futures import ThreadPoolExecutor
import logging
import time
import multiprocessing as mp

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


def gen_arguments(subnet: List[int], port: int, command: str, client_addrs: List[str] = None):  # TODO: Only support *.*.*.0/24
    data = bytes(command, encoding='ascii')

    if client_addrs is None:
        postfix = subnet[-1]
        while postfix < 256:
            yield {'addr': ".".join(map(lambda x: str(x), subnet[:3])) + '.' + str(postfix), 'port': port, 'data': data}
            postfix += 1
    else:
        for addr in client_addrs:
            yield {'addr': addr, 'port': port, 'data': data}


def print_help():
    print("\
Commands: \n\
    > restart\n\
    > ping\n\
    > shutdown\n\
    > update\n\
    > cali_reset\n\
    > cali_acc\n\
    > cali_mag\n\
    > start\n\
    > stop\n\
    > gy_enable\n\
    > gy_disable\n\
    > gy_status\n\
    > gy_imm\n\
    > gy_setup\n\
    > gy_scale\n\
    > id\n\
    > ver\n\
    > blink_set\n\
    > blink_get\n\
    > blink_start\n\
    > blink_stop\n\
    > blink_off\n\
    > v_verison_shutdown\n\
    > sleep\n\
    > hold*\n\
    > quit - quit this tool\n\n")


def control(port: int, client_queue: mp.Queue = None):
    # Get subnet, like [10,52,24,0]
    try:
        subnet: List[int] = list(map(lambda x: int(x), input("Input subnet of IMUs, e.g. 10.52.24.0\n> ").split(".")))
    except ValueError:
        logging.info("Wrong input, use default value(10.52.24.0)")
        subnet = [10, 52, 24, 0]

    print(f"Welcome to Inertial Measurement Unit control system \n\n \
Sending to {subnet}\n")
    print_help()

    if client_queue is not None:
        client_addrs: set[str] = set([])
    else:
        client_addrs = None

    try:
        while True:
            if client_addrs is not None:
                print(f"Online clients: {client_addrs}")
            if client_queue is not None:
                while not client_queue.empty():
                    client_addrs.add(str(client_queue.get()))
            command = input("> ")
            if command == '':
                continue
            elif command in ['quit', 'q']:
                break
            elif command in ['hold', 'h']:
                hold(subnet, port)
                continue

            with ThreadPoolExecutor(64) as executor:
                if client_addrs is not None:
                    print(f"Sending to: {client_addrs}")
                for ret in executor.map(tcp_send_bytes, gen_arguments(subnet, port, command, list(client_addrs))):
                    if len(ret['msg']) > 0:
                        print(f"{(ret['addr'])} return: {ret['msg']}")

            print_help()
    except KeyboardInterrupt:
        print("Exitting")
        return


if __name__ == '__main__':
    control(18888)
