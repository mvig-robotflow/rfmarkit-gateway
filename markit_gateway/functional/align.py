import glob
import json
import os
from typing import Dict, List

import numpy as np

import os.path as osp
import quaternionic
from scipy.spatial.transform import Rotation as R
from scipy.spatial.transform import Slerp
import pickle

from markit_gateway.functional.ellipse import EllipseFitter


def quaternionic_slerp(*args):
    return quaternionic.slerp(*args)


def get_averaged_global_timestamp_us(imu_device_id_mapping, min_timestamp_us, method):
    _raw = np.array([
        imu_device_id_mapping[imu_id]['timestamp'][np.where(imu_device_id_mapping[imu_id][method] >= min_timestamp_us)[0].min()] for imu_id in imu_device_id_mapping.keys()
    ])

    _mean = _raw.mean(axis=0)
    _std = np.std(_raw)
    _var = np.var(_raw)

    return int(_mean), _std, _var


def align_measurement(measurement_basedir: str, method: str = 'tsf_timestamp') -> Dict[str, Dict[str, np.ndarray]]:
    _linear_interp_fields = {
        'accel': ['accel_x', 'accel_y', 'accel_z'],
        'gyro': ['gyro_x', 'gyro_y', 'gyro_z'],
        'mag': ['mag_x', 'mag_y', 'mag_z'],
    }
    _quat_interp_fields = {
        'quat': ['quat_x', 'quat_y', 'quat_z', 'quat_w'],
    }
    _euler_interp_fields = {
        'euler': ['roll', 'pitch', 'yaw'],
    }

    filenames_list: List[str] = glob.glob(os.path.join(measurement_basedir, '*.npz'))
    imu_device_id_mapping = {
        osp.basename(filename).split('_')[1].split('.')[0]: np.load(filename) for filename in filenames_list
    }
    # imu_device_id_mapping = {
    #     k:v for k, v in imu_device_id_mapping.items() if k != 'all'
    # }
    master_id = list(imu_device_id_mapping.keys())[0]
    min_timestamp_us = max([item['tsf_timestamp'].min() for item in imu_device_id_mapping.values()])
    max_timestamp_us = min([item['tsf_timestamp'].max() for item in imu_device_id_mapping.values()])
    _ts = imu_device_id_mapping[master_id][method]
    master_tsf_timestamp_us = _ts[(_ts >= min_timestamp_us) & (_ts <= max_timestamp_us)]
    master_global_to_tsf, std, var = get_averaged_global_timestamp_us(imu_device_id_mapping, min_timestamp_us, method)
    master_global_timestamp_us = (master_tsf_timestamp_us - master_tsf_timestamp_us[0]) + master_global_to_tsf

    interp_res = dict()
    meta_data = dict()
    for imu_id, imu_data in imu_device_id_mapping.items():
        interp_res[imu_id] = dict()
        for dst_field, src_field in _linear_interp_fields.items():
            interp_res[imu_id][dst_field] = np.concatenate(
                [
                    np.expand_dims(
                        np.interp(
                            master_tsf_timestamp_us,
                            imu_data[method].squeeze(),
                            imu_data[name].squeeze()
                        ),
                        axis=1
                    ) for name in src_field
                ],
                axis=1
            )

        for dst_field, src_field in _quat_interp_fields.items():
            _quat = np.concatenate(
                [imu_data[name] for name in src_field],
                axis=1
            )
            slerp = Slerp(
                imu_data[method].squeeze(),
                R.from_quat(_quat)
            )
            interp_res[imu_id][dst_field] = slerp(master_tsf_timestamp_us).as_quat()

        for dst_field, src_field in _euler_interp_fields.items():
            _euler = np.concatenate(
                [imu_data[name] for name in src_field],
                axis=1
            )
            slerp = Slerp(
                imu_data[method].squeeze(),
                R.from_euler('xyz', _euler, degrees=True)
            )
            interp_res[imu_id][dst_field] = slerp(master_tsf_timestamp_us).as_euler(seq='xyz', degrees=True)

        interp_res[imu_id]['timestamp'] = master_global_timestamp_us
        interp_res[imu_id]['tsf_timestamp'] = master_tsf_timestamp_us

    meta_data['general'] = {
        '.master_id': master_id
    }
    meta_data['timestamp'] = {
        'master_global_to_tsf': master_global_to_tsf,
        'std': std,
        'var': var,
    }
    meta_data['ellipse'] = {
        imu_id: EllipseFitter.fit(imu_data['mag']) for imu_id, imu_data in interp_res.items()
    }

    pickle.dump(interp_res, open(os.path.join(measurement_basedir, f'imu.pkl'), 'wb'))
    json.dump(meta_data, open(os.path.join(measurement_basedir, f'imu.json'), 'w'), indent=4)
    # np.savez(os.path.join(measurement_basedir, f'imu_all.npz'), **interp_res)
    return interp_res


if __name__ == '__main__':
    align_measurement(r'C:\Users\robotflow\Desktop\rfimu-interface\imu_data\imu_mem_2023-04-18_193003')
