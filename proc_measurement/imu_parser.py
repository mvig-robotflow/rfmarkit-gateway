import logging
from typing import List, Dict, BinaryIO

import numpy as np
import ctypes
import struct


class ch_imu_data_t(ctypes.Structure):
    _fields_ = [
        ("id", ctypes.c_uint32),
        ("acc", ctypes.c_float * 3),
        ("gyr", ctypes.c_float * 3),
        ("mag", ctypes.c_float * 3),
        ("eul", ctypes.c_float * 3),
        ("quat", ctypes.c_float * 4),
        ("timestamp", ctypes.c_uint32)
    ]


ch_imu_data_t_fmt = "I3f3f3f3f4fI"
hi229_dgram_meta_t_fmt = "q12sBqi"

logging.basicConfig(level=logging.INFO)

DATA_FORMAT = {
    "accel_x": [5, 4],
    "accel_y": [7, 6],
    "accel_z": [9, 8],
    "gyro_x": [11, 10],
    "gyro_y": [13, 12],
    "gyro_z": [15, 14],
    "roll": [17, 16],
    "pitch": [19, 18],
    "yaw": [21, 20],
    "temp": [24, 23],
    "mag_x": [26, 25],
    "mag_y": [28, 27],
    "mag_z": [30, 29],
}
META_FORMAT = {
    "data": [0, 32],
    "timestamp": [32, 40],
    "id": [40, 52],
    "gy_scale": [52, 53],
    "start_timestamp": [53, 61],
    "uart_buffer_len": [61, 65],
}
DATA_DIVIDER = {
    "accel_x": 4 / 65536,
    "accel_y": 4 / 65536,
    "accel_z": 4 / 65536,
    "gyro_x": 500 / 65536,
    "gyro_y": 500 / 65536,
    "gyro_z": 500 / 65536,
    "roll": 1 / 100,
    "pitch": 1 / 100,
    "yaw": 1 / 100,
    "temp": 1 / 100,
    "mag_x": 4 / 65536,
    "mag_y": 4 / 65536,
    "mag_z": 4 / 65536,
}


# def extract_meta(data):
#     """Extract meta info from data
#
#     Args:
#         data ([type]): [description]
#     """
#     timestamp: float = sum([data[idx] * 0x100 ** (idx)
#                             for idx in range(0,8)]) / 1e6  # Already the compensated time
#     device_id: str = ''.join([chr(data[idx]) for idx in range(8, 20)])
#     scale = data[20]  # '0x8b'
#     start_timestamp = sum(
#         [data[idx] * 0x100 ** (idx - 21) for idx in
#          range(21,29)]) / 1e6
#
#     uart_buffer_len = sum(
#         [data[idx] * 0x100 ** (idx - 29) for idx in
#          range(29, 33)])
#
#     return timestamp, device_id, scale, start_timestamp, uart_buffer_len

def extract_meta(data):
    """Extract meta info from data

    Args:
        data ([type]): [description]
    """
    timestamp: float = data[0]# Already the compensated time
    device_id: str = ''.join([chr(data[1][idx]) for idx in range(len(data[1]))])
    scale = data[2]  # '0x8b'
    start_timestamp = data[3]
    uart_buffer_len = data[4]

    return timestamp, device_id, scale, start_timestamp, uart_buffer_len

def parse_data(data):
    res: dict = {
        "accel_x": 0.0,
        "accel_y": 0.0,
        "accel_z": 0.0,
        "gyro_x": 0.0,
        "gyro_y": 0.0,
        "gyro_z": 0.0,
        "roll": 0.0,
        "pitch": 0.0,
        "yaw": 0.0,
        "temp": 0.0,
        "mag_x": 0.0,
        "mag_y": 0.0,
        "mag_z": 0.0,
    }

    timestamp, id, scale, start_timestamp, uart_buffer_len = extract_meta(data['meta_data'])

    res["accel_x"] = data['imu_data'][1]
    res["accel_y"] = data['imu_data'][2]
    res["accel_z"] = data['imu_data'][3]
    res["gyro_x"] = data['imu_data'][4]
    res["gyro_y"] = data['imu_data'][5]
    res["gyro_z"] = data['imu_data'][6]
    res["roll"] = data['imu_data'][10]
    res["pitch"] = data['imu_data'][11]
    res["yaw"] = data['imu_data'][12]
    res["mag_x"] = data['imu_data'][7]
    res["mag_y"] = data['imu_data'][8]
    res["mag_z"] = data['imu_data'][9]

    res["timestamp"] = timestamp
    res["id"] = id
    res["start_timestamp"] = start_timestamp
    res["uart_buffer_len"] = uart_buffer_len
    return res


class IMUParser:
    ADDR = 0xe5
    BLOCK_SZ: int = 0x1000

    def __init__(self) -> None:
        self.buf: np.ndarray = np.zeros(shape=(100), dtype=np.uint8)
        self.cursor: int = 0
        self.start_reg: int = 0
        self.length: int = 0
        self.data_valid: bool = False
        self.meta_valid: bool = False

    def _reset(self):
        self.cursor = 0
        self.start_reg = 0
        self.length = 0
        self.data_valid = False
        self.meta_valid = False
        self.buf.fill(0)

    # TODO: There are still room of optimization
    def _sync(self, read_buf: bytes):
        res: List[Dict[str, float]] = []
        if len(read_buf) <= 0:
            # TODO: Think about what we should do with an empty file
            return res

        for idx in range(len(read_buf)):
            if read_buf[idx] == self.ADDR:
                _start_idx = idx + 1
                _end_idx = _start_idx + struct.calcsize(ch_imu_data_t_fmt)
                data_valid = sum(read_buf[_start_idx: _end_idx]) % 0x100 == read_buf[_end_idx + 1]
                if data_valid:
                    _end_idx = _start_idx + 1 + struct.calcsize(ch_imu_data_t_fmt) + struct.calcsize(
                        hi229_dgram_meta_t_fmt)
                    data_valid = sum(read_buf[idx: _end_idx]) % 0x100 == read_buf[_end_idx + 1]
                    if data_valid:
                        return {
                            "sync_start_idx": _start_idx - 1,
                            "dgram_length": _end_idx - _start_idx + 3,
                            "imu_offset": 1,
                            "imu_length": struct.calcsize(ch_imu_data_t_fmt),
                            "imu_fmt": ch_imu_data_t_fmt,
                            "meta_offset": _start_idx + 2 + struct.calcsize(ch_imu_data_t_fmt),
                            "meta_length": struct.calcsize(hi229_dgram_meta_t_fmt),
                            "meta_fmt": hi229_dgram_meta_t_fmt
                        }
                else:
                    continue

            self.cursor += 1

        return None

    def _parse(self, read_buf, fmt):
        res: List[Dict] = []
        start_idx = fmt['sync_start_idx']
        try:
            while start_idx + fmt['dgram_length'] < len(read_buf):
                imu_data = struct.unpack(ch_imu_data_t_fmt, read_buf[start_idx + fmt['imu_offset']:start_idx + fmt['imu_offset'] + fmt['imu_length']])
                meta_data = struct.unpack(hi229_dgram_meta_t_fmt, read_buf[start_idx + fmt['meta_offset']:start_idx + fmt['meta_offset'] + fmt['meta_length']])
                res.append(parse_data({"imu_data": imu_data, "meta_data": meta_data}))

                start_idx += fmt['dgram_length']
        except Exception as e:
            pass

        return res

    def __call__(self, f: BinaryIO) -> List[Dict[str, float]]:
        read_buf = f.read()
        fmt = self._sync(read_buf)
        res = self._parse(read_buf, fmt)

        return res


if __name__ == '__main__':
    gy = IMUParser()
    with open(
            "C:\\Users\\liyutong\\projectExchange\\imu-interface\\tcp_broker\\imu_data\\imu_mem_2022-01-27_195105\\process_0_384.dat",
            'rb') as f:
        res = gy(f)

    print(res)
