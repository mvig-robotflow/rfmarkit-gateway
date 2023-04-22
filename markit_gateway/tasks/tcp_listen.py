import logging
import multiprocessing as mp
import os
import socket
import time
from typing import List

import select

from markit_gateway.common import IMUConnection
from markit_gateway.config import BrokerConfig
from .tcp_process import tcp_process_task


def tcp_listen_task(config: BrokerConfig,
                    tag: str,
                    stop_ev: mp.Event,
                    finish_ev: mp.Event,
                    client_info_queue: mp.Queue = None,
                    imu_state_queue: mp.Queue = None,
                    ) -> None:
    logger = logging.getLogger('tcp_listen_task')
    logger.setLevel(logging.DEBUG) if config.debug else logger.setLevel(logging.INFO)

    measurement_basedir = os.path.join(config.base_dir, tag)
    # Check the existence of output directory
    if not os.path.exists(measurement_basedir):
        os.makedirs(measurement_basedir)

    client_queues: List[mp.Queue] = [mp.Queue() for _ in range(config.n_procs)]

    # Create client processors
    client_procs: List[mp.Process] = [
        mp.Process(None,
                   tcp_process_task,
                   f"tcp_process_{i}",
                   (
                       client_queues[i],
                       config,
                       measurement_basedir,
                       i,
                       stop_ev,
                       imu_state_queue
                   ),
                   daemon=False) for i in range(config.n_procs)
    ]
    [p.start() for p in client_procs]

    n_client: int = 0
    # Set up the server
    server_socket: socket.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((config.data_addr, config.data_port))
    server_socket.listen(config.n_procs)
    logger.info(f"binding address {config.data_addr}:{config.data_port}")

    try:
        while True:
            client_read_ready_fds, _, _ = select.select([server_socket.fileno()], [], [], 1)
            if len(client_read_ready_fds) > 0:
                client_socket, (client_address, client_port) = server_socket.accept()
                logger.info(f"new client {client_address}:{client_port}")

                new_client = IMUConnection(client_socket,
                                           client_address,
                                           client_port,
                                           render_packet=config.render_packet,
                                           imu_port=config.imu_port,
                                           proc_id=n_client % config.n_procs,
                                           update_interval_s=config.update_interval_s)
                if client_info_queue is not None:
                    client_info_queue.put(new_client)

                client_socket.setblocking(False)  # Non-blocking

                client_socket.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)  # Set keep-alive
                if hasattr(socket, "TCP_KEEPIDLE") and hasattr(socket, "TCP_KEEPINTVL") and hasattr(socket,
                                                                                                    "TCP_KEEPCNT"):
                    client_socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPIDLE, 60)
                    client_socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPINTVL, 60)
                    client_socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPCNT, 3)

                # Evenly distribute client to subprocesses
                client_queues[n_client % config.n_procs].put(new_client)
                n_client += 1

            if not any([proc.is_alive() for proc in client_procs]) or stop_ev.is_set():
                break
            else:
                time.sleep(0.01)
    except KeyboardInterrupt:
        logger.info("tcp_listen process capture keyboard interrupt")

    logger.info("joining all processes")
    for proc in client_procs:
        logger.debug(f"joining {proc}")
        proc.join()

    server_socket.close()
    finish_ev.set()
    logger.debug(f"all processes are joined")
