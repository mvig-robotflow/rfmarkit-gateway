import io
import logging
import multiprocessing as mp
import os
import socket
import time
from typing import Any, Dict, BinaryIO, List, Tuple
from io import BufferedWriter
import select

from config import TCP_BUFF_SZ


def insert_data(f: BinaryIO, data: bytes):
    """Insert data to FileIO database (file)

    Args:
        f (BinaryIO): file handler
        data (bytes): string formated data
    """
    if data is None:
        return
    f.write(data)


def unregister_fd(fd: int,
                  client_sockets: Dict[int, socket.socket],
                  client_read_fds: List[int],
                  file_handles: Dict[int, BinaryIO]):
    """Unregister file descriptor

    Args:
        fd (int): [description]
        client_sockets (Dict[int, socket.socket]): [description]
        client_read_fds:
        file_handles (Dict[int, BinaryIO]): [description]
    """
    client_sockets[fd].shutdown()
    client_sockets[fd].close()
    file_handles[fd].close()
    client_read_fds.remove(fd)
    del client_sockets[fd]
    del file_handles[fd]


class ClientRegistration:
    def __init__(self, basedir, proc_id):
        self.basedir = basedir
        self.proc_id = proc_id
        self.socks: Dict[int, socket.socket] = {}
        self.fds = []
        self.ids: Dict[int, Dict[str, Any]] = {}
        self.handles: Dict[int, BinaryIO] = {}
        pass

    def register(self, sock: socket.socket, addr, port):
        # Registration of New client:
        # - get client socket
        # - store client socket in `socks`
        # - open file handle for this client
        fd = sock.fileno()
        self.socks[fd] = sock
        self.fds.append(fd)
        self.ids[fd] = {
            'addr': addr,
            'port': port,
            'transmited': False
        }
        if fd not in self.handles.keys():
            self.handles[fd] = open(
                os.path.join(self.basedir, f'process_{str(self.proc_id)}_{fd}.dat'), 'ab')
        else:
            logging.warning(f"The fd: {fd} already has related file handle")

    def __len__(self):
        return len(self.fds)

    def get_info(self, fd) -> Tuple[str, int]:
        return self.ids[fd]['addr'], self.ids[fd]['port']

    def unregister(self, fd):
        self.socks[fd].shutdown(2)
        self.socks[fd].close()
        del self.socks[fd]

        self.handles[fd].close()
        del self.handles[fd]

        self.fds.remove(fd)

    def close(self):
        for fd in self.fds:
            self.socks[fd].shutdown(2)
            self.socks[fd].close()
            self.handles[fd].close()
        self.__init__(self.basedir, self.proc_id)

    def mark_as_online(self, fd):
        self.ids[fd]['transmited'] = True
        addr, port = self.get_info(fd)
        logging.info(f"Client {addr}:{port} started sending data")

    def flush(self):
        for key, handle in self.handles.items():
            handle.close()


def tcp_process_task(client_socket_queue: mp.Queue, measurement_basedir: str, proc_id: int, stop_ev: mp.Event):
    registration = ClientRegistration(measurement_basedir, proc_id)

    try:
        while True:
            if not client_socket_queue.empty():
                new_client: Dict[str: Any] = client_socket_queue.get()
                registration.register(new_client["socket"], new_client["addr"], new_client["port"])

            if len(registration) > 0:
                client_read_ready_fds, _, _ = select.select(registration.fds, [], [], 1)
                for fd in client_read_ready_fds:
                    try:
                        data = registration.socks[fd].recv(TCP_BUFF_SZ)
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
