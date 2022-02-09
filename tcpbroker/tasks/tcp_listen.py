import logging
import multiprocessing as mp
import tqdm
import socket
from typing import List, Dict, Union, Any
import time
from config import N_PROC
from .tcp_process import tcp_process_task
import os
from config import  DATA_DIR

MAX_LISTEN = 64


def tcp_listen_task(address: str, port: int, measurement_name: str, client_addr_queue: mp.Queue = None) -> None:
    # Create client listeners

    # Check the existence of output directory
    measurement_basedir = os.path.join(DATA_DIR, measurement_name)
    # Use lock to avoid duplicate creation
    if not os.path.exists(measurement_basedir):
        os.makedirs(measurement_basedir)
    client_queues: List[mp.Queue] = [mp.Queue(maxsize=16) for _ in range(N_PROC)]

    client_procs: List[mp.Process] = [
        mp.Process(None,
                   tcp_process_task,
                   f"tcp_process_{i}", (
                       client_queues[i],
                       measurement_basedir,
                       i,
                   ),
                   daemon=False) for i in range(N_PROC)
    ]
    with tqdm.tqdm(range(len(client_procs))) as pbar:
        for proc in client_procs:  # Start all listeners
            proc.start()
            pbar.update()

    n_client: int = 0

    # Setup the server
    server_socket: socket.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((address, port))
    server_socket.listen(MAX_LISTEN)
    logging.info(f"Binding address {address}:{port}")

    try:
        while True:

            client_socket, (client_address, client_port) = server_socket.accept()
            logging.info(f"New client {client_address}:{client_port}")

            if client_addr_queue is not None:
                client_addr_queue.put(client_address)

            client_socket.setblocking(True)  # Non-blocking

            client_socket.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)  # Set keep-alive
            if hasattr(socket, "TCP_KEEPIDLE") and hasattr(socket, "TCP_KEEPINTVL") and hasattr(socket,
                                                                                                "TCP_KEEPCNT"):
                client_socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPIDLE, 60)
                client_socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPINTVL, 60)
                client_socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPCNT, 3)

            # Evenly distribute client to subprocesses
            client_info: Dict[str, Union[socket, Any]] = {
                "addr": client_address,
                "port": client_port,
                "socket": client_socket
            }
            client_queues[n_client % N_PROC].put(client_info)
            n_client += 1

            if not any([proc.is_alive() for proc in client_procs]):
                break
            else:
                time.sleep(0.01)
    except KeyboardInterrupt:
        logging.info("Main process capture keyboard interrupt")

    logging.info("Joining all processes")
    for proc in client_procs:
        logging.debug(f"Joining {proc}")
        proc.join()

    server_socket.close()
