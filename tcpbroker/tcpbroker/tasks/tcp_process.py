import logging
import multiprocessing as mp
import os
import select
import socket
import time
from typing import Any, Dict, BinaryIO, List, Tuple

from tcpbroker.config import BrokerConfig
from tcpbroker.common import ClientRegistry

logging.basicConfig(level=logging.INFO)


def insert_data(f: BinaryIO, data: bytes):
    """Insert data to FileIO database (file)

    Args:
        f (BinaryIO): file handler
        data (bytes): string formated data
    """
    if data is None:
        return
    f.write(data)


def tcp_process_task(client_socket_queue: mp.Queue, config: BrokerConfig, measurement_basedir: str, proc_id: int, stop_ev: mp.Event):
    registration = ClientRegistry(measurement_basedir, proc_id)
    recv_size = config.TCP_BUFF_SZ

    try:
        while True:
            if not client_socket_queue.empty():
                new_client: Dict[str: Any] = client_socket_queue.get()
                registration.register(new_client["socket"], new_client["addr"], new_client["port"])

            if len(registration) > 0:
                client_read_ready_fds, _, _ = select.select(registration.fds, [], [], 1)
                for fd in client_read_ready_fds:
                    try:
                        data = registration.socks[fd].recv(recv_size)
                    except Exception as e:
                        logging.warning(e)
                        logging.warning(f"Client {registration.ids[fd]['addr']}:{registration.ids[fd]['port']} disconnected unexpectedly")
                        registration.unregister(fd)
                        continue
                    if len(data) <= 0:
                        logging.warning(f"Client {registration.ids[fd]['addr']}:{registration.ids[fd]['port']} disconnected unexpectedly")
                        registration.unregister(fd)
                        continue

                    if not registration.ids[fd]['transmited']:
                        registration.mark_as_online(fd)

                    insert_data(registration.handles[fd], data)

            if stop_ev.is_set():
                logging.debug("Clossing sockets")
                registration.close()
                return

            else:
                time.sleep(0.01)
    except KeyboardInterrupt:
        logging.debug(f"process {proc_id} is exitting")
        registration.close()
