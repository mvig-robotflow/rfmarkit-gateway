import glob
import os
import tqdm
import json
import urllib
from typing import List, Dict, Any, Union
import uuid
from datetime import timedelta
import logging

from minio import Minio
import zipfile
import numpy as np
from imu_parser import IMUParser

logging.basicConfig(level=logging.INFO)
MEASUREMENT_KEYS: List[str] = [
    'id', 'timestamp', 'accel_x', 'accel_y', 'accel_z', 'gyro_x', 'gyro_y', 'gyro_z', 'mag_x', 'mag_y', 'mag_z', 'pitch', 'roll', 'yaw', "start_timestamp","uart_buffer_len"
]


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
        ret = {
            'status': True,
            'error': "",
            'bucket_name': bucket_name,
            'object_name': object_name,
            'url': url
        }  # Return the object info
        return ret

    except Exception as err:
        return {'status': False, 'error': str(err)}


def download_file_oss(endpoint: str,
                      bucket_name: str,
                      access_key: str,
                      secret_key: str,
                      object_name: str,
                      file: str = '') -> Union[None, Dict[str, str]]:
    """Upload a file to MinIO OSS

    Args:
        args (ArgumentParser): should contain following attributes:
            - args.endpoint: str, url
            - args.access_key: str
            - args.secret_key: str

    Returns:
        Dict[str, str]: {$BUCKET:$NAME}
    """
    if len(file) <= 0: 
        file = object_name

    minioClient = Minio(endpoint, access_key=access_key, secret_key=secret_key, secure=False)  # Create MinIO client
    try:
        minioClient.fget_object(bucket_name, object_name, file) # download
        return {'status': True, 'file': file}

    except Exception as err:
        return {'status': False, 'error': str(err)}


def get_mem_from_url(url: str, object_name: str) -> str:
    logging.info(f"Downloading dataset from {url}")

    tmp_filename = f'/tmp/{object_name}'
    # Download archive with urllib
    try:
        urllib.request.urlretrieve(url, tmp_filename)
    except Exception:
        if os.path.exists(tmp_filename):
            os.remove(tmp_filename)
        raise Exception

    measuremnet_name: str = os.path.splitext(object_name)[0]

    # Unzip and get measurement name
    with zipfile.ZipFile(tmp_filename) as f:
        f.extractall()

    # Remove the archive file
    os.remove(tmp_filename)

    return measuremnet_name


def vectorize_to_np(record_list: List[Dict[str, Any]], keys: List[str]) -> Dict[str, np.ndarray]:
    """Vectorizing record

    Args:
        record_list (List[Dict[str, Any]]): List of records, each record is a bundled dictionary
        keys (List[str]): keys to extract from records

    Returns:
        Dict[str, np.ndarray]: A dictionary in which keys are desired and values are numpy arrays
    """
    assert len(keys) > 0
    assert len(record_list) > 0
    res = {}
    for key in keys:
        res[key] = np.expand_dims(np.array([record[key] for record in record_list]), axis=-1)

    # Verify length
    _length: int = len(res[keys[0]])
    for key in keys:
        if _length != len(res[key]):
            raise ValueError("Not every attribute has the same length")

    return res


def convert_measurement(measurement_basedir: str, delete_dat: bool = False) -> Dict[str, Dict[str, np.ndarray]]:
    filenames_list: List[str] = glob.glob(os.path.join(measurement_basedir, '*.dat'))
    all_measurement: Dict[str, list] = {}
    all_measurement_np: Dict[str, Dict[str, np.ndarray]] = {}
    imu_parser = IMUParser()

    # Scatter measurement point
    for filename in filenames_list:
        with open(filename, 'rb') as f:
            points = imu_parser(f)
            for point in points:
                point_id = point['id']
                if point_id not in all_measurement.keys():
                    all_measurement[point_id] = []
                all_measurement[point_id].append(point)
    logging.info(f"Got measurement from {len(all_measurement)} client")

    # Convert to numpy
    with tqdm.tqdm(len(all_measurement)) as pbar:
        pbar.update()
        for key in all_measurement.keys():
            all_measurement_np[key] = vectorize_to_np(all_measurement[key], MEASUREMENT_KEYS)

    # Clean dat files
    if delete_dat:
        map(lambda x: os.remove(x), filenames_list)

    # Dump numpy array
    for imu_id in all_measurement_np.keys():
        np.savez(os.path.join(measurement_basedir, f'imu_{imu_id}.npz'), **all_measurement_np[imu_id])
    """example
    >>> import numpy as np
    >>> npfile = np.load('./imu_mem_2021-10-21_211859/imu_84f7033b3e78.npz')
    >>> npfile.files
    ['id', 'timestamp', 'accel_x', 'accel_y', 'accel_z', 'gyro_x',  'gyro_y', 'gyro_z', 'pitch', 'roll', 'yaw']
    >>> npfile['timestamp']
    array([[1.63482358e+15],
          [1.63482358e+15],
          [1.63482358e+15],
          ...,
          [1.63482235e+15],
          [1.63482235e+15],
          [1.63482235e+15]])
    """

    return all_measurement_np


if __name__ == '__main__':
    res = convert_measurement('/home/liyutong/Tasks/imu-node-deploy/tcp_broker/imu_data/imu_mem_2021-11-02_010812')
    print(res)