import socket
import multiprocessing as mp
import select
import logging
from typing import List

from .tcp_process import tcp_process_task

from config import N_PROC, POLL_READ

def tcp_listen_task(address: str, port: int, measurement_name: str, max_listen: int = 64) -> None:
    # Create client listeners
    client_queues: List[mp.Queue] = [mp.Queue(maxsize=4) for _ in range(N_PROC)]
    system_lock = mp.Lock()
    client_procs: List[mp.Process] = [
        mp.Process(None, tcp_process_task, f"tcp_process_{i}", (
            client_queues[i],
            system_lock,
            measurement_name,
            i,
        ), daemon=False) for i in range(N_PROC)
    ]
    for proc in client_procs: # Start all listeners
        proc.start()

    n_client: int = 0

    # Setup the server
    server_socket: socket.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((address, port))
    server_socket.listen(max_listen)
    logging.info(f"Binding address {address}:{port}")

    poller = select.poll()
    poller.register(server_socket.fileno(), POLL_READ)

    try:
        while True:
            epoll_list = poller.poll(1000)

            for fd, events in epoll_list:
                if events & (select.POLLIN | select.POLLPRI) and fd is server_socket.fileno():
                    client_socket, (client_address, client_port) = server_socket.accept()
                    logging.info(f"New client {client_address}:{client_port}")
                    client_socket.setblocking(0)  # Non-blocking

                    client_socket.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)  # Set keep-alive
                    if hasattr(socket, "TCP_KEEPIDLE") and hasattr(socket, "TCP_KEEPINTVL") and hasattr(socket, "TCP_KEEPCNT"):
                        client_socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPIDLE, 60)
                        client_socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPINTVL, 60)
                        client_socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPCNT, 3)

                    # Evenly distribute client to subprocesses
                    client_queues[n_client % N_PROC].put(client_socket)
                    n_client += 1

            if not any([proc.is_alive() for proc in client_procs]):
                break
    except KeyboardInterrupt:
        logging.info("Main process capture keyboard interrupt")

    logging.info("Joining all processes")
    for proc in client_procs:
        logging.debug(f"Joining {proc}")
        proc.join()
    
    server_socket.close()
