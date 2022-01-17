import logging
import multiprocessing as mp
import os
import socket
import time
from typing import Any, Dict, BinaryIO

import select

from config import TCP_BUFF_SZ
from helpers import insert_data, unregister_fd


def tcp_process_task(client_socket_queue: mp.Queue, measurement_basedir: str, proc_id: int):
    client_sockets: Dict[int, socket.socket] = {}
    client_read_fds = []
    client_identifiers: Dict[int, Dict[str, Any]] = {}
    file_handles: Dict[int, BinaryIO] = {}

    try:
        while True:
            if not client_socket_queue.empty():
                # Registration of New client:
                # - get client socket
                # - store client socket in `client_sockets`
                # - open file handle for this client
                new_client: Dict[str: Any] = client_socket_queue.get()
                new_client_socket = new_client["socket"]
                new_client_addr = new_client["addr"]
                new_client_port = new_client["port"]
                new_client_fd = new_client_socket.fileno()

                client_sockets[new_client_fd] = new_client_socket
                client_read_fds.append(new_client_fd)
                client_identifiers[new_client_fd] = {
                    "addr": new_client_addr,
                    "port": new_client_port,
                    "transmited": False
                }

                if new_client_fd not in file_handles.keys():
                    file_handles[new_client_fd] = open(
                        os.path.join(measurement_basedir, f'process_{str(proc_id)}_{new_client_fd}.dat'), 'ab')
                else:
                    logging.warning(f"The fd: {new_client_fd} already has related file handle")

            if len(client_sockets) > 0:
                client_read_ready_fds, _, _ = select.select(client_read_fds, [], [])
                for fd in client_read_ready_fds:
                    client_addr = client_identifiers[fd]['addr']
                    client_port = client_identifiers[fd]['port']
                    data = client_sockets[fd].recv(TCP_BUFF_SZ)
                    if len(data) <= 0:
                        logging.info(f"Client {client_addr}:{client_port} disconnected unexpectedly")
                        unregister_fd(fd, client_sockets, client_read_fds, file_handles)
                        continue

                    if not client_identifiers[fd]["transmited"]:
                        client_identifiers[fd]["transmited"] = True
                        logging.info(f"Client {client_addr}:{client_port} started sending data")
                    insert_data(file_handles[fd], data)  # TODO: Print info about client
                    # TODO: Optimize with BytesIO

            else:
                time.sleep(0.01)
    except KeyboardInterrupt:
        logging.debug(f"process {proc_id} is exitting")
        for key in file_handles.keys():
            file_handles[key].close()
