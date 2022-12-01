import dataclasses
import logging
import multiprocessing as mp
import os
import socket
from typing import Dict, BinaryIO, Tuple, Union

from .render import IMURender


@dataclasses.dataclass()
class IMUConnection:
    socket: socket.socket
    addr: str
    port: int
    render_packet: bool = False
    proc_id: int = None

    tcp_fd: int = None
    active: bool = False

    render: IMURender = None
    buffer: BinaryIO = None
    out_queue: mp.Queue = None

    def __post_init__(self):
        self.tcp_fd = self.socket.fileno()
        self.active = False

    def set_backend(self,
                    filename: str,
                    out_queue: mp.Queue = None):
        if self.render_packet:
            self.render = IMURender(filename, out_queue=out_queue)  # TODO update_interval_s is not used
        else:
            self.buffer = open(filename, 'ab')

    def close(self):
        if getattr(self.socket, '_closed'):
            # If not closed by imu, then the case is that we intend to close socket for some reason
            # -> use shutdown to notify imu
            self.socket.shutdown(2)
        self.socket.close()

        if self.buffer is not None:
            self.buffer.close()

    def update(self, data: bytes = None):
        if data is not None:
            if self.render is not None:
                self.render.update(data)
            elif self.buffer is not None:
                self.buffer.write(data)
            else:
                raise ValueError("No buffer or render object")


class ClientRepo:
    def __init__(self, base_dir, proc_id, imu_stat_queue: mp.Queue = None):
        self.base_dir = base_dir
        self.proc_id = proc_id
        self.imu_stat_queue = imu_stat_queue

        self.index_by_fd: Dict[int, IMUConnection] = {}

        self.logger = logging.getLogger("client_repo")
        pass

    def register(self, client: IMUConnection):
        # Registration of New client
        fd = client.tcp_fd
        if client.tcp_fd not in self.index_by_fd.keys():
            client.set_backend(os.path.join(self.base_dir, f'process_{str(self.proc_id)}_{fd}.dat'), out_queue=self.imu_stat_queue)
            self.index_by_fd[fd] = client
        else:
            logging.warning(f"the fd: {fd} is already registered with client {self.index_by_fd[fd]}")

    def __len__(self):
        return len(self.index_by_fd)

    def get_info(self, fd) -> Tuple[str, int]:
        return self.index_by_fd[fd].addr, self.index_by_fd[fd].port

    def unregister(self, fd):
        self.index_by_fd[fd].close()
        del self.index_by_fd[fd]

    def close(self):
        for _, client in self.index_by_fd.items():
            client.close()
        self.__init__(self.base_dir, self.proc_id)

    def mark_as_online(self, fd):
        self.index_by_fd[fd].active = True
        addr, port = self.get_info(fd)
        self.logger.info(f"client {addr}:{port} started sending data")
