import logging
import multiprocessing as mp
import os
import select
import socket
import time
from typing import Any, Dict, BinaryIO, List, Tuple

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
    client_sockets[fd].shutdown(socket.SHUT_RDWR)
    client_sockets[fd].close()
    file_handles[fd].close()
    client_read_fds.remove(fd)
    del client_sockets[fd]
    del file_handles[fd]
    
class ClientRegistry:
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
        # Detect if the socket is closed by imu
        if getattr(self.socks[fd], '_closed'):
            # If not closed by imu, then the case is that we intend to close socket for some reason
            # -> use shutdown to notify imu
            self.socks[fd].shutdown(2)
        self.socks[fd].close()
        del self.socks[fd]

        self.handles[fd].close()
        del self.handles[fd]

        self.fds.remove(fd)

    def close(self):
        for fd in self.fds:
            if getattr(self.socks[fd], '_closed'):
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
