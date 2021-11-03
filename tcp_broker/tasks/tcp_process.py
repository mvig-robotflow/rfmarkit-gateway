import socket
import multiprocessing as mp
import select
import logging
import os
import time

from io import FileIO
from typing import Any, Dict

from config import  TCP_BUFF_SZ, POLL_READ, POLL_TIMEOUT_MS, DATA_DIR
from helpers import unregister_fd, insert_data

def tcp_process_task(client_socket_queue: mp.Queue, system_lock: mp.Lock,measurement_name: str, proc_id: int):
    # Check the existence of output directory
    measurement_basedir = os.path.join(DATA_DIR, measurement_name)
    # Use lock to avoid duplicate creation
    system_lock.acquire()
    if not os.path.exists(measurement_basedir):
        os.makedirs(measurement_basedir)
    system_lock.release()

    poller: select.poll = select.poll()
    client_sockets: Dict[int, socket.socket] = {}
    file_handles: Dict[int, FileIO] = {}
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
                poller.register(new_client_fd, POLL_READ)
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
                    logging.warn(f"The fd: {fd} already has related file handle")

            if len(client_sockets) > 0:
                epoll_list = poller.poll(POLL_TIMEOUT_MS)

                for fd, events in epoll_list:
                    client_addr = client_identifiers[fd]["addr"]
                    client_port = client_identifiers[fd]["port"]

                    # Disconnection
                    if events & select.POLLHUP:
                        # Shutdown socket and close data file on socket close
                        
                        logging.info(f"Client {client_addr}:{client_port} disconnected")
                        unregister_fd(fd, poller, client_sockets, file_handles)
                        continue

                    # Incomming data
                    elif events & select.POLLIN:
                        data = client_sockets[fd].recv(TCP_BUFF_SZ)
                        if len(data) <= 0 or events & select.POLLHUP:
                            logging.info(f"Client {client_addr}:{client_port} disconnected unexpectedly")
                            unregister_fd(fd, poller, client_sockets, file_handles)
                            continue
                        
                        if not client_identifiers[fd]["transmited"]:
                            client_identifiers[fd]["transmited"] = True
                            logging.info(f"Client {client_addr}:{client_port} started sending data")
                        insert_data(file_handles[fd], data) #TODO: Print info about client

                    else:
                        logging.warn(f"Unhandled event {events}")
            else:
                time.sleep(0.01)
    except KeyboardInterrupt:
        logging.debug(f"process {proc_id} is exitting")
        for key in file_handles.keys():
            file_handles[key].close()