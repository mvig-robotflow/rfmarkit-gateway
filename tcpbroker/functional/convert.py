import glob
import logging
import os
from typing import Dict, List

import numpy as np
import tqdm

from tcpbroker.common import IMUParser
from .vector import vectorize_to_np


def convert_measurement(measurement_basedir: str, delete_dat: bool = False) -> Dict[str, Dict[str, np.ndarray]]:
    _logger = logging.getLogger('convert_measurement')

    MEASUREMENT_KEYS: List[str] = [
        'id', 'timestamp', 'accel_x', 'accel_y', 'accel_z', 'gyro_x', 'gyro_y', 'gyro_z', 'mag_x', 'mag_y', 'mag_z', 'quat_w', 'quat_x', 'quat_y', 'quat_z', 'pitch', 'roll', 'yaw', "uart_buffer_len"
    ]

    filenames_list: List[str] = glob.glob(os.path.join(measurement_basedir, '*.dat'))
    all_measurement: Dict[str, list] = {}
    all_measurement_np: Dict[str, Dict[str, np.ndarray]] = {}
    imu_parser = IMUParser()

    # Scatter measurement point
    for filename in filenames_list:
        with open(filename, 'rb') as f:
            points = imu_parser(f)
            for point in points:
                point_id = str(point['id'])
                if point_id not in all_measurement.keys():
                    all_measurement[point_id] = []
                all_measurement[point_id].append(point)
    _logger.info(f"Got measurement from {len(all_measurement)} client")

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
    res = convert_measurement(r"C:\Users\liyutong\Desktop\rfimu-interface\imu_data\imu_mem_2022-10-27_193652")
    print(res)
