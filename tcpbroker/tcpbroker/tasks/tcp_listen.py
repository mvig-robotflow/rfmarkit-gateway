import logging
import multiprocessing as mp
import os
import select
import socket
import time
from typing import List, Dict, Union, Any

import tqdm

from tcpbroker.config import BrokerConfig
from .tcp_process import tcp_process_task


def tcp_listen_task(address: str,
                    port: int,
                    config: BrokerConfig,
                    measurement_name: str,
                    stop_ev: mp.Event,
                    finish_ev: mp.Event,
                    client_addr_queue: mp.Queue = None,
                    ) -> None:
    # Create client listeners

    # Check the existence of output directory
    measurement_basedir = os.path.join(config.DATA_DIR, measurement_name)
    # Use lock to avoid duplicate creation
    if not os.path.exists(measurement_basedir):
        os.makedirs(measurement_basedir)
    client_queues: List[mp.Queue] = [mp.Queue() for _ in range(config.N_PROCS)]

    client_procs: List[mp.Process] = [
        mp.Process(None,
                   tcp_process_task,
                   f"tcp_process_{i}", (
                       client_queues[i],
                       config,
                       measurement_basedir,
                       i,
                       stop_ev,
                   ),
                   daemon=False) for i in range(config.N_PROCS)
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
    server_socket.listen(config.N_PROCS)
    logging.info(f"Binding address {address}:{port}")

    try:
        while True:
            client_read_ready_fds, _, _ = select.select([server_socket.fileno()], [], [], 1)
            if len(client_read_ready_fds) > 0:
                client_socket, (client_address, client_port) = server_socket.accept()
                logging.info(f"New client {client_address}:{client_port}")

                if client_addr_queue is not None:
                    client_addr_queue.put(client_address)

                client_socket.setblocking(False)  # Non-blocking

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
                client_queues[n_client % config.N_PROCS].put(client_info)
                n_client += 1

            if not any([proc.is_alive() for proc in client_procs]) or stop_ev.is_set():
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
    finish_ev.set()
    logging.debug(f"All processes are joined")
