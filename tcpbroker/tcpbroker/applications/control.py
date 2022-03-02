import logging
import multiprocessing as mp
import socket
from concurrent.futures import ThreadPoolExecutor
from typing import List, Union

from tcpbroker.config import BrokerConfig


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
        # logging.warning(f"Socket timeout for {addr}")
        pass

    return {"addr": addr, "msg": reply}


def gen_arguments(subnet: List[int], port: int, command: str,
                  client_addrs: set = None):
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


def probe(subnet: List[int], port: int, client_addrs: Union[set, None]) -> set:
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
        for ret in executor.map(tcp_send_bytes, gen_arguments(subnet, port, 'blink_get', client_addrs)):
            if len(ret['msg']) > 0:
                res_no_crlf = ret['msg'].split('\n')[0]
                res.add(ret['addr'])
                print(f"{(ret['addr'])} return: {res_no_crlf}")

    return res


def broadcast_command(subnet: List[int], port: int, command: str, client_addrs: Union[set, None]):
    # loop = asyncio.get_event_loop()
    # send_tasks = [asyncio.ensure_future(tcp_send_bytes(arguments)) for arguments in gen_arguments(subnet, port, command, client_addrs)]
    # loop.run_until_complete(asyncio.wait(send_tasks))
    with ThreadPoolExecutor(256) as executor:
        if client_addrs is not None:
            print(f"Sending to: {client_addrs}")
        for ret in executor.map(tcp_send_bytes, gen_arguments(subnet, port, command, client_addrs)):
            if len(ret['msg']) > 0:
                res_no_crlf = ret['msg'].split('\n')[0]
                print(f"{(ret['addr'])} return: {res_no_crlf}")


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


def control(port: int, config: BrokerConfig, client_queue: mp.Queue = None):
    # Get subnet, like [10,52,24,0]
    subnet = list(map(lambda x: int(x), config.DEFAULT_SUBNET.split("."))) if config.DEFAULT_SUBNET is not None else None
    if subnet is None:
        try:
            subnet: List[int] = list(
                map(lambda x: int(x), input("Input subnet of IMUs, e.g. 10.53.24.0\n> ").split(".")))
        except ValueError:
            logging.info("Wrong input, use default value(192.168.1.0)")
            subnet = [192, 168, 1, 0]

        except KeyboardInterrupt:
            print("Control Exiting")
            return

    print(f"Welcome to Inertial Measurement Unit control system \n\n Sending to {subnet}\n")
    print_help()

    if client_queue is not None:
        client_addrs: Union[None, set] = set([])
    else:
        client_addrs = None

    try:
        while True:
            if client_addrs is not None:
                print(f"Online clients [{len(client_addrs)}] : {client_addrs}")
            if client_queue is not None:
                while not client_queue.empty():
                    client_addrs.add(str(client_queue.get()))
            command = input("> ")
            if command == '':
                continue
            elif command in ['probe', 'p']:
                client_addrs = probe(subnet, port, None)
                continue
            elif command in ['quit', 'q']:
                break

            broadcast_command(subnet, port, command, client_addrs)

            # print_help()
    except KeyboardInterrupt:
        print("Control Exiting")
        return


if __name__ == '__main__':
    control(18888, BrokerConfig('./config.json'))
