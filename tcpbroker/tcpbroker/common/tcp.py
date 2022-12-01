import dataclasses
import logging
import socket
from concurrent.futures import ThreadPoolExecutor
from typing import Union, List, Dict, Any


@dataclasses.dataclass()
class IMUControlMessage:
    addr: str
    msg: str
    success: bool = False


def tcp_send_bytes(addr: str, port: int, data: Union[str, bytes]):
    data = data.encode(encoding='ascii')
    reply = ''

    logging.debug(f"sending {data} to {addr}:{port}")

    ctrl_socket: socket.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    ctrl_socket.settimeout(2)  # Magic timeout
    try:
        ctrl_socket.connect((addr, port))
    except Exception as err:
        if isinstance(err, socket.timeout) or isinstance(err, ConnectionRefusedError):
            return IMUControlMessage(addr=addr, msg=reply, success=False)
        else:
            logging.debug(f"{err} for {addr}")
            return IMUControlMessage(addr=addr, msg=str(err), success=False)

    try:
        ctrl_socket.send(data)
        while True:
            res = str(ctrl_socket.recv(1024), encoding='ascii')
            if len(res) <= 0:
                break
            else:
                reply += res

    except socket.timeout:
        # logging.warning(f"Socket timeout for {addr}")
        pass

    if len(reply) > 0:
        return IMUControlMessage(addr=addr, msg=reply, success=True)
    else:
        return IMUControlMessage(addr=addr, msg=reply, success=False)


def tcp_broadcast_command(addresses: List[str], port: int, command_string: str, verbose: bool = True) -> List[Dict[str, Any]]:
    """
    Probe clients using id
    Args:
        addresses:
        port:
        command_string:
        verbose:

    Returns:

    """
    results: List[Dict[str, Any]] = []
    with ThreadPoolExecutor(0x100) as executor:
        if addresses is not None and verbose:
            logging.debug(f"sending to: {addresses}")
        for ret in executor.map(lambda x: tcp_send_bytes(*x), [(addr, port, command_string) for addr in addresses]):
            if len(ret.msg) > 0:
                res_no_crlf = ret.msg.split('\n')[0]
                if verbose:
                    logging.debug(f"{ret.addr} return: {res_no_crlf}")
                results.append({'addr': ret.addr, 'res': res_no_crlf})
    return results
