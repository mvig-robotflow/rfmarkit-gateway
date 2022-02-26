import logging
import multiprocessing as mp
import socket
from concurrent.futures import ThreadPoolExecutor
from typing import List, Union
from config import CONFIG


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

    try:
        ctrl_socket.send(data)
        while True:
            reply += str(ctrl_socket.recv(1024), encoding='ascii')
    except socket.timeout:
        logging.warning(f"Socket timeout for {addr}")

    return {"addr": addr, "msg": reply}


def gen_arguments(subnet: List[int], port: int, command: str,
                  client_addrs: set[str] = None):
    # FIXME: Only support *.*.*.0/24
    data = bytes(command, encoding='ascii')

    if client_addrs is None:
        postfix = int(subnet[-1])
        while postfix < 256:
            yield {'addr': ".".join(map(lambda x: str(x), subnet[:3])) + '.' + str(postfix), 'port': port, 'data': data}
            postfix += 1
    else:
        for addr in client_addrs:
            yield {'addr': addr, 'port': port, 'data': data}


def probe(subnet: List[int], port: int, client_addrs: set[str]) -> set:
    """
    Probe clients using ping
    Args:
        subnet:
        port:
        client_addrs:

    Returns:

    """
    res = set()
    with ThreadPoolExecutor(64) as executor:
        if client_addrs is not None:
            print(f"Sending to: {client_addrs}")
        for ret in executor.map(tcp_send_bytes, gen_arguments(subnet, port, 'ping\n', client_addrs)):
            if len(ret['msg']) > 0:
                res.add(ret['addr'])
    return res


def broadcast_command(subnet: List[int], port: int, command: str, client_addrs: set[str]):
    # loop = asyncio.get_event_loop()
    # send_tasks = [asyncio.ensure_future(tcp_send_bytes(arguments)) for arguments in gen_arguments(subnet, port, command, client_addrs)]
    # loop.run_until_complete(asyncio.wait(send_tasks))
    with ThreadPoolExecutor(256) as executor:
        if client_addrs is not None:
            print(f"Sending to: {client_addrs}")
        for ret in executor.map(tcp_send_bytes, gen_arguments(subnet, port, command, client_addrs)):
            if len(ret['msg']) > 0:
                print(f"{(ret['addr'])} return: {ret['msg']}")


def print_help():
    print("\
Commands: \n\
    > ping\n\
    > restart|shutdown\n\
    > update\n\
    > imu_cali_[reset|acc|mag]\n\
    > start|stop\n\
    > imu_[enable|disable|status|imm|setup|scale|debug]\n\
    > id\n\
    > ver\n\
    > time\n\
    > blink_[set|get|start|stop|off]\n\
    > v_{CONFIG_FIRMWARE_VERSION}_shutdown\n\
    > self_test \n\
    > always_on \n\
    > varget|varset\n\
    > probe* - probe client in a subnet\n\
    > quit* - quit this tool\n\n")


def control(port: int, client_queue: mp.Queue = None):
    # Get subnet, like [10,52,24,0]
    if CONFIG is not None and "default_subnet" in CONFIG.keys():
        subnet = list(map(lambda x: int(x), CONFIG['default_subnet'].split(".")))
    else:
        try:
            subnet: List[int] = list(map(lambda x: int(x), input("Input subnet of IMUs, e.g. 10.53.24.0\n> ").split(".")))
        except ValueError:
            logging.info("Wrong input, use default value(10.53.24.0)")
            subnet = [10, 53, 24, 0]

        except KeyboardInterrupt:
            print("Control Exiting")
            return

    print(f"Welcome to Inertial Measurement Unit control system \n\n Sending to {subnet}\n")
    print_help()

    if client_queue is not None:
        client_addrs: Union[None, set[str]] = set([])
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
            elif command in ['probe', 'p']:
                client_addrs = probe(subnet, port, client_addrs)
            elif command in ['quit', 'q']:
                break

            broadcast_command(subnet, port, command, client_addrs)

            # print_help()
    except KeyboardInterrupt:
        print("Control Exiting")
        return


if __name__ == '__main__':
    control(18888)
