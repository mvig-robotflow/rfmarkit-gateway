import logging
import multiprocessing as mp
import os
import socket
import time
from typing import Any, Dict, BinaryIO
from config import TCP_BUFF_SZ
from helpers import insert_data, unregister_fd


def tcp_process_task(client_socket_queue: mp.Queue, measurement_basedir: str, proc_id: int):

    client_sockets: Dict[int, socket.socket] = {}
    file_handles: Dict[int, BinaryIO] = {}
    client_identifiers: Dict[int, Dict[str, Any]] = {}

    try:
        while True:
            if not client_socket_queue.empty():
                # Registration of New client:
                # - get client socket
                # - store client socket in `client_sockets`
                # - register socket.fileno() to poller
                # - open file handle for this client
                new_client: Dict[str: Any] = client_socket_queue.get()

                new_client_socket = new_client["socket"]
                new_client_fd = new_client_socket.fileno()
                client_sockets[new_client_fd] = new_client_socket
                client_identifiers[new_client_fd] = \
                    {
                        "addr": new_client["addr"],
                        "port": new_client["port"],
                        "transmited": False
                    }
                if new_client_fd not in file_handles.keys():
                    file_handles[new_client_fd] = open(
                        os.path.join(measurement_basedir, f'process_{str(proc_id)}_{new_client_fd}.dat'), 'ab')
                else:
                    logging.warning(f"The fd: {new_client_fd} already has related file handle")

            if len(client_sockets) > 0:
                for fd in list(client_sockets.keys()):
                    client_addr = client_identifiers[fd]['addr']
                    client_port = client_identifiers[fd]['port']
                    data = client_sockets[fd].recv(TCP_BUFF_SZ)
                    if len(data) <= 0:
                        logging.info(f"Client {client_addr}:{client_port} disconnected unexpectedly")
                        unregister_fd(fd, client_sockets, file_handles)
                        continue

                    if not client_identifiers[fd]["transmited"]:
                        client_identifiers[fd]["transmited"] = True
                        logging.info(f"Client {client_addr}:{client_port} started sending data")
                    insert_data(file_handles[fd], data)  # TODO: Print info about client

            else:
                time.sleep(0.01)
    except KeyboardInterrupt:
        logging.debug(f"process {proc_id} is exitting")
        for key in file_handles.keys():
            file_handles[key].close()
