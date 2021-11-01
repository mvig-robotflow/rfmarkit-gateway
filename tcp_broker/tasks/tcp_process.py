import socket
import multiprocessing as mp
import select
import logging
import os
import time

from io import FileIO
from typing import Dict

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

    try:
        while True:
            if not client_socket_queue.empty():
                # Registration of New client:
                # - get client socket
                # - store client socket in `client_sockets`
                # - register socket.fileno() to poller
                # - open file handle for this client
                new_client_socket: socket.socket = client_socket_queue.get()
                new_client_fd = new_client_socket.fileno()
                poller.register(new_client_fd, POLL_READ)
                client_sockets[new_client_fd] = new_client_socket
                if new_client_fd not in file_handles.keys():
                    file_handles[new_client_fd] = open(
                        os.path.join(measurement_basedir, f'process_{str(proc_id)}_{new_client_fd}.dat'), 'ab')
                else:
                    logging.warn(f"The fd: {fd} already has related file handle")

            if len(client_sockets) > 0:
                epoll_list = poller.poll(POLL_TIMEOUT_MS)

                for fd, events in epoll_list:
                    # Incomming data
                    
                    # Disconnection
                    if events & select.POLLHUP:
                        # Shutdown socket and close data file on socket close
                        logging.info("Client disconnected")
                        unregister_fd(fd, poller, client_sockets, file_handles)
                        continue
                    
                    elif events & select.POLLIN:
                        data = client_sockets[fd].recv(TCP_BUFF_SZ)
                        if len(data) <= 0 or events & select.POLLHUP:
                            logging.info("Client disconnected unexpectedly")
                            unregister_fd(fd, poller, client_sockets, file_handles)
                            continue

                        insert_data(file_handles[fd], data)

                    else:
                        logging.warn(f"Unhandled event {events}")
            else:
                time.sleep(0.01)
    except KeyboardInterrupt:
        logging.debug(f"process {proc_id} is exitting")
        for key in file_handles.keys():
            file_handles[key].close()