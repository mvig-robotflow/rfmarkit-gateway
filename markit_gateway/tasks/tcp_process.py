import logging
import multiprocessing as mp
import time
from typing import BinaryIO

import select

from markit_gateway.common import ClientRepo, IMUConnection
from markit_gateway.config import BrokerConfig

logging.basicConfig(level=logging.INFO)


def insert_data(f: BinaryIO, data: bytes):
    """Insert data to FileIO database (file)

    Args:
        f (BinaryIO): file handler
        data (bytes): string formated data
    """
    if data is None:
        return
    f.write(data)


def tcp_process_task(client_socket_queue: mp.Queue,
                     config: BrokerConfig,
                     base_dir: str,
                     proc_id: int,
                     stop_ev: mp.Event,
                     imu_state_queue: mp.Queue = None):
    _logger = logging.getLogger('tcp_process_task')
    _logger.setLevel(logging.DEBUG) if config.debug else _logger.setLevel(logging.INFO)

    registration = ClientRepo(base_dir, proc_id, imu_state_queue=imu_state_queue)
    recv_size = config.tcp_buff_sz

    try:
        while True:
            if not client_socket_queue.empty():
                new_client: IMUConnection = client_socket_queue.get()
                registration.register(IMUConnection(new_client.socket,
                                                    new_client.addr,
                                                    new_client.port,
                                                    render_packet=new_client.render_packet,
                                                    proc_id=new_client.proc_id,
                                                    update_interval_s=new_client.update_interval_s))

            if len(registration) > 0:
                client_read_ready_fds, _, _ = select.select(list(registration.index_by_fd.keys()), [], [], 1)
                for fd in client_read_ready_fds:
                    cli = registration.index_by_fd[fd]
                    try:
                        data = cli.socket.recv(recv_size)
                    except Exception as e:
                        _logger.warning(e)
                        _logger.warning(f"client {cli.addr}:{cli.port} disconnected unexpectedly")
                        registration.unregister(fd)
                        continue
                    if len(data) <= 0:
                        _logger.warning(f"client {cli.addr}:{cli.port} disconnected unexpectedly")
                        registration.unregister(fd)
                        continue

                    if not cli.active:
                        registration.mark_as_online(fd)

                    cli.update(data)
                    if imu_state_queue is not None and cli.render is not None:
                        imu_state_queue.put(cli.render.state)

            if stop_ev.is_set():
                _logger.debug("closing sockets")
                registration.close()
                return

            else:
                time.sleep(0.01)
    except KeyboardInterrupt:
        _logger.debug(f"process {proc_id} is exiting")
        registration.close()
