import json
import math

import numpy as np
import scipy
import transforms3d as t3d
import matplotlib.pyplot as plt
from scipy import signal

from typing import List, Any, Dict, Union, Tuple

from helpers import vectorize_to_np


class IMUAlgorithm(object):
    def __init__(self) -> None:
        pass

    @classmethod
    def rpy_to_pose_mat_np(cls, rpy_data: np.ndarray) -> np.ndarray:
        """Convert roll-pitch-yaw data to transform matrix

        Args:
            ryp_data (np.ndarray): 2-D matrix
            [[r0,p0,y0],[r1,p1,y1],...]

        Returns:
            np.ndarray: [description]
        """
        length = rpy_data.shape[0]
        pose_mat = np.empty(shape=(length, 3, 3))
        for idx in range(length):
            pose_mat[idx] = t3d.euler.euler2mat(*rpy_data[idx], 'rxyz')
        return pose_mat

    @classmethod
    def visualize_3d(cls, data: np.ndarray, timestamp: np.ndarray, title: str):
        fig = plt.figure(figsize=(32, 8))

        ax = fig.add_subplot(121, projection='3d')
        ax.scatter(data[:, 0], data[:, 1], data[:, 2], c=timestamp)
        ax.set_xlabel(title + '-X', fontdict={'size': 15, 'color': 'red'})
        ax.set_ylabel(title + '-Y', fontdict={'size': 15, 'color': 'red'})
        ax.set_zlabel(title + '-Z', fontdict={'size': 15, 'color': 'red'})

        ax = fig.add_subplot(122)
        ax.scatter(timestamp, data[:, 0], s=2, c='r')
        ax.scatter(timestamp, data[:, 1], s=2, c='g')
        ax.scatter(timestamp, data[:, 2], s=2, c='b')
        ax.set_title(title)

        plt.show()

    @classmethod
    def filter_accel(cls, accel: np.ndarray, band: Tuple[float, float] = (0.005, 0.9999)):
        res = np.copy(accel)
        b, a = signal.butter(7, band, 'bandpass')
        res[:, 0] = signal.filtfilt(b, a, accel[:, 0])
        res[:, 1] = signal.filtfilt(b, a, accel[:, 1])
        res[:, 2] = signal.filtfilt(b, a, accel[:, 2])
        return res

    @classmethod
    def get_gravity_projection(cls, rpy, local_gravity: np.ndarray = np.array([0, 0, -9.8]), thresh: int = 50):
        _pose_mat = t3d.euler.euler2mat(rpy[:thresh, 0].mean(), rpy[:thresh, 1].mean(), rpy[:thresh, 2].mean())
        g = _pose_mat @ local_gravity  # gravity projected to imu coordinate
        return g

    @classmethod
    def get_accel_offset(accel: np.ndarray, g: np.ndarray, thresh: int = 100) -> np.ndarray:
        reading = np.mean(accel[:thresh, :], axis=0)
        offset = reading - g
        return offset

    @classmethod
    def zero_vel_determination(vel: np.ndarray,
                               gyro: np.ndarray,
                               accel: np.ndarray,
                               thresh: Tuple[float] = (0.1, 0.1, 0.5, 0.1)) -> bool:
        if vel.shape[0] > 0 and gyro.shape[0] > 0 and accel.shape[0] > 0:
            vel_mean = np.sqrt(np.sum(np.mean(vel, axis=0)**2))
            gyro_mean = np.sqrt(np.sum(np.mean(gyro, axis=0)**2))
            gyro_std = np.mean(np.std(gyro, axis=0))
            accel_mean = np.sqrt(np.sum(np.mean(accel, axis=0)**2))
            accel_std = np.mean(np.std(accel, axis=0))
            # print(vel_mean, gyro_mean, gyro_std, accel_mean, accel_std)
            if gyro_mean < thresh[0] and gyro_std < thresh[1] and accel_mean < thresh[2] and accel_std < thresh[3]:
                return True
            else:
                return False
        else:
            return False

    @classmethod
    def parse_record(cls, arr: np.ndarray, g: float = 9.8):
        c = np.pi / 180  # deg->rad conversion
        _res = arr
        _accel = np.hstack([_res['accel_x'] * g,_res['accel_y'] * g,_res['accel_z'] * g])
        _rpy = np.hstack([_res['roll'] * c,_res['pitch'] * c,_res['yaw'] * c])
        _gyro = np.hstack([_res['gyro_x'] * c,_res['gyro_y'] * c,_res['gyro_z'] * c])
        _pose_mat = cls.rpy_to_pose_mat_np(_rpy)
        _timestamp = _res['time']
        return _accel, _rpy, _gyro, _pose_mat, _timestamp
    
    @classmethod
    def reconstruct(accel_raw: np.ndarray, rpy: np.ndarray, gyro: np.ndarray, pose_mat: np.ndarray, timestamp: np.ndarray)