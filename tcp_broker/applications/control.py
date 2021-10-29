import socket
import select
import logging
logging.basicConfig(level=logging.INFO)

from config import POLL_READ

def control(port: int):
    address: str = '0.0.0.0' # TODO: Magic Numbers
    max_listen: int = 64 # TODO: 
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

    except KeyboardInterrupt:
        logging.info("Main process capture keyboard interrupt")
    pass