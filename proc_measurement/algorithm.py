import numpy as np
import transforms3d as t3d
import matplotlib.pyplot as plt
from scipy import signal

from typing import List, Any, Dict, Union, Tuple

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
    def visualize_1d(cls, data: np.ndarray, timestamp: np.ndarray, title: str):
        fig = plt.figure(figsize=(10, 8))

        ax = fig.add_subplot(111)
        ax.scatter(timestamp, data, s=2)
        ax.set_title(title)

        plt.show()

    @classmethod
    def filter_accel_bandpass(cls, accel: np.ndarray, band: Tuple[float, float] = (0.005, 0.9999)):
        res = np.copy(accel)
        b, a = signal.butter(7, band, 'bandpass')
        res[:, 0] = signal.filtfilt(b, a, accel[:, 0])
        res[:, 1] = signal.filtfilt(b, a, accel[:, 1])
        res[:, 2] = signal.filtfilt(b, a, accel[:, 2])
        return res

    @classmethod
    def filter_accel_middle(cls, accel: np.ndarray, windows_sz: int = 5):
        res = np.copy(accel)
        for idx in range(len(accel) - windows_sz):
            res[idx:idx + windows_sz] = np.repeat(np.expand_dims(np.mean(res[idx:idx + windows_sz], axis=0), axis=0),
                                                  windows_sz,
                                                  axis=0)
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
    def zero_vel_determination(cls,
                               vel: np.ndarray,
                               gyro: np.ndarray,
                               accel: np.ndarray,
                               thresh: Tuple[float] = (0.2, 0.2, 5, 0.5)) -> bool:
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
    def unpack_npz(cls, npzfile: np.ndarray, unit_g: float = 9.764, trim_thresh: int = 0, **kwargs):
        accel_raw = np.squeeze(np.stack([-1 * npzfile['accel_x'], npzfile['accel_y'], npzfile['accel_z']], axis=1)) * unit_g
        gyro = np.squeeze(np.stack([npzfile['gyro_x'], npzfile['gyro_y'], npzfile['gyro_z']], axis=1))
        rpy = np.squeeze(np.stack([npzfile['roll'], npzfile['pitch'], npzfile['yaw']], axis=1)) * np.pi / 180
        mag = np.squeeze(np.stack([npzfile['mag_x'], npzfile['mag_y'], npzfile['mag_z']], axis=1))
        timestamp = npzfile['timestamp']
        pose_mat = cls.rpy_to_pose_mat_np(rpy)

        # Trim
        accel_raw = accel_raw[trim_thresh:]
        gyro = gyro[trim_thresh:]
        rpy = rpy[trim_thresh:]
        pose_mat = pose_mat[trim_thresh:]
        timestamp = timestamp[trim_thresh:]
        return {'accel_raw': accel_raw, 'gyro': gyro, 'mag': mag, 'rpy': rpy, 'pose_mat': pose_mat, 'timestamp': timestamp}

    @classmethod
    def substract_gravity(cls,
                          accel_raw,
                          rpy,
                          timestamp,
                          pose_mat,
                          measurement_bias: np.array = np.array([0, 0, 0], dtype=np.float32),
                          **kwargs):
        GRAVITY_SHANGHAI = np.array([0, 0, -9.7964]) # TODO: Use measured value
        accel_raw -= measurement_bias
        # TODO: 50 is a magic number, the thresh (short)
        accel = np.copy(accel_raw)
        # Project gravity to local coordinate, then substract accel initial readings (mesured g) with projected gravity
        # assumed_gain = np.array([1,1,1])
        g_projection = cls.get_gravity_projection(rpy, GRAVITY_SHANGHAI, 50)
        print(f"g_projection={g_projection}")
        # accel_bias = cls.get_accel_offset(accel, g_projection, 50)
        # print(f'accel_bias={accel_bias}")
        # accel -= accel_bias

        # Sustract gravity
        gravity = np.empty_like(accel)
        for i in range(len(timestamp)):
            gravity[i] = pose_mat[i] @ GRAVITY_SHANGHAI
        accel -= gravity

        # filter accel
        # accel = cls.filter_accel(accel, (0.005,0.999))
        print(f'accel.mean={np.mean(accel[:50,:],axis=0)}')

        for i in range(len(timestamp)):
            accel[i] = np.linalg.inv(pose_mat[i]) @ accel[i]

        return {'accel': accel, 'gravity': gravity}

    @classmethod
    def run_zv_detection(cls, accel, gyro, timestamp, window_sz: int = 3, **kwargs):
        # calc velocity, with zero velocity update policy
        zero_vel = np.zeros_like(timestamp, dtype=np.int16)
        vel = np.zeros_like(accel)
        for i in range(len(timestamp) - 1):
            if cls.zero_vel_determination(vel[i - window_sz:i, :], gyro[i - window_sz:i, :], accel[i - window_sz:i, :]):
                vel[i + 1] = 0
                zero_vel[i] = 1
            else:
                vel[i + 1] = vel[i] + 0.5 * (accel[i + 1] + accel[i]) * (timestamp[i + 1] - timestamp[i])
        return {'vel': vel, 'zero_vel': zero_vel}

    @classmethod
    def run_zv_calibration(cls, zero_vel, accel_raw, rpy, gravity, **kwargs) -> Union[None, np.array]:
        cali_points = []
        for idx, status in enumerate(zero_vel):
            if status > 0:
                cali_points.append({
                    'idx': idx,
                    'mes': accel_raw[idx],
                    'rpy': rpy[idx],
                    'g': gravity[idx],
                    'vel': np.array([0, 0, 0], dtype=np.float32)
                })
        if (len(cali_points) <= 0):
            return None

        mes = np.zeros(shape=(len(cali_points), 3))
        real = np.zeros(shape=(len(cali_points), 3))
        for idx, point in enumerate(cali_points):
            mes[idx] = point['mes']
            real[idx] = gravity[point['idx']]
        # Plan1 mes = real + bias + noise

        bias = mes.mean(axis=0) - real.mean(axis=0)  # bias of accel_raw
        print(f"accel_raw.bias={bias}")

        return bias, cali_points

    @classmethod
    def run_vel_calibration(cls, vel: np.array, cali_points: List[Dict[str, Any]]):
        vel_offset = np.zeros_like(vel)
        last_point = {'idx': 0, 'vel': np.array([0, 0, 0], dtype=np.float32)}
        for point in cali_points:
            vel_offset[last_point['idx']:point['idx']]
            vel_offset[last_point['idx']:point['idx']] = np.linspace(vel_offset[last_point['idx']],
                                                                     vel[point['idx']] - -point['vel'],
                                                                     point['idx'] - last_point['idx'])
            last_point = point

        return vel_offset

    @classmethod
    def run_pos_construction(cls, vel, timestamp, **kwargs):
        # calc displacement
        # Mid-value integration
        pos = np.zeros_like(vel)
        for i in range(len(timestamp) - 1):
            pos[i + 1] = pos[i] + 0.5 * (vel[i + 1] + vel[i]) * (timestamp[i + 1] - timestamp[i])
        return pos

    @classmethod
    def reconstruct(cls, measurement_filepath: str):
        ctx: Dict[str, np.array] = cls.unpack_npz(np.load(measurement_filepath))  # e.g. ./imu_abcdef123456.npz
        print(ctx.keys())

        # # Filter accel_raw
        # accel_raw = cls.filter_accel_middle(ctx['accel_raw'])
        # ctx['accel_raw'] = accel_raw

        # Calibrate accel
        acc_gravity: Dict[str, np.array] = cls.substract_gravity(ctx['accel_raw'], ctx['rpy'], ctx['timestamp'],
                                                                 ctx['pose_mat'])
        ctx = {**ctx, **acc_gravity}  # Merge

        vel_zerovel: Dict[str, np.array] = cls.run_zv_detection(ctx['accel'], ctx['gyro'], ctx['timestamp'])
        ctx = {**ctx, **vel_zerovel}  # Merge

        accel_raw_bias, cali_points = cls.run_zv_calibration(ctx['zero_vel'], ctx['accel_raw'], ctx['rpy'], ctx['gravity'])
        print(f"accel_raw_bias={accel_raw_bias}")
        ctx['cali_points'] = cali_points

        if accel_raw_bias is not None:
            ctx['accel_raw'] = ctx['accel_raw'] - accel_raw_bias

        # Re-run steps using the calibrated accel
        acc_gravity: Dict[str, np.array] = cls.substract_gravity(ctx['accel_raw'], ctx['rpy'], ctx['timestamp'], ctx['pose_mat'])
        ctx.update(**acc_gravity)

        vel_zerovel: Dict[str, np.array] = cls.run_zv_detection(ctx['accel'], ctx['gyro'], ctx['timestamp'])
        ctx.update(**vel_zerovel)

        vel_offset = cls.run_vel_calibration(ctx['vel'], ctx['cali_points'])
        ctx['vel_offset'] = vel_offset

        pos = cls.run_pos_construction(ctx['vel'] - vel_offset, ctx['timestamp'])

        return ctx, pos

