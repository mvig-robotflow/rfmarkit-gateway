import os
import json
import select
import socket
import uuid

from typing import Any, Union, Dict
from io import FileIO
from datetime import timedelta

from minio import Minio

import requests

def upload_file_oss(endpoint: str,
                    bucket_name: str,
                    access_key: str,
                    secret_key: str,
                    file: str,
                    object_name: str = '') -> Union[None, Dict[str, str]]:
    """Upload a file to MinIO OSS

    Args:
        args (ArgumentParser): should contain following attributes:
            - args.endpoint: str, url
            - args.access_key: str
            - args.secret_key: str

    Returns:
        Dict[str, str]: {$BUCKET:$NAME}
    """
    minioClient = Minio(endpoint, access_key=access_key, secret_key=secret_key, secure=False)  # Create MinIO client
    try:
        if len(object_name) <= 0:
            object_name = str(uuid.uuid1()) + os.path.splitext(file)[-1]  # Generate unique object name
        else:
            object_name = object_name

        minioClient.fput_object(bucket_name, object_name, file)  # Upload object
        url = minioClient.presigned_get_object(bucket_name, object_name, expires=timedelta(days=2))
        ret = {'status': True, 
               'error': "",
               'bucket_name': bucket_name, 
               'object_name': object_name, 
               'url': url}  # Return the object info
        return ret

    except Exception as err:
        return {'status': False, 'error': str(err)}

def invoke_data_process_task(service_apihost: str, 
                             payload: Dict[str, Any]):
    headers = {'Content-Type': 'application/json'}
    response = requests.post(url=service_apihost,
                             headers=headers,
                             data=json.dumps(payload))
                             
    return response.json()


def insert_data(f: FileIO, data: str):
    """Insert data to FileIO database (file)

    Args:
        f (FileIO): file handler
        data (str): string formated data
    """
    if data is None:
        return
    f.write(data)

def unregister_fd(fd: int, poller: select.poll, client_sockets: Dict[int, socket.socket], file_handles: Dict[int, FileIO]):
    """Unregister file descriptor

    Args:
        fd (int): [description]
        poller (select.poll): [description]
        client_sockets (Dict[int, socket.socket]): [description]
        file_handles (Dict[int, FileIO]): [description]
    """
    poller.unregister(fd)
    client_sockets[fd].close()
    file_handles[fd].close()
    del client_sockets[fd]
    del file_handles[fd]

