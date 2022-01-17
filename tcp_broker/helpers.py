from typing import Dict, BinaryIO
import socket

def insert_data(f: BinaryIO, data: bytes):
    """Insert data to FileIO database (file)

    Args:
        f (BinaryIO): file handler
        data (bytes): string formated data
    """
    if data is None:
        return
    f.write(data)

def unregister_fd(fd: int, client_sockets: Dict[int, socket.socket], file_handles: Dict[int, BinaryIO]):
    """Unregister file descriptor

    Args:
        fd (int): [description]
        client_sockets (Dict[int, socket.socket]): [description]
        file_handles (Dict[int, BinaryIO]): [description]
    """
    client_sockets[fd].close()
    file_handles[fd].close()
    del client_sockets[fd]
    del file_handles[fd]

