import logging
import struct
from typing import List, Dict, BinaryIO

import numpy as np


class IMUParser:
    ADDR = 0xe5
    BLOCK_SZ: int = 0x1000
    ch_imu_data_t_fmt = "I3f3f3f3f4ffI"
    hi229_dgram_meta_t_fmt = "=qqIi12s"

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

    @staticmethod
    def verify_packet(buf, chksum: int) -> bool:
        arr = np.frombuffer(buf, dtype=np.uint8)
        arr_chksum = np.bitwise_xor.reduce(arr)
        return arr_chksum == chksum

    def _sync(self, read_buf: bytes):
        """
        Magic Sync Algorithm.
        See imu-esp-node (C code)
        Args:
            read_buf:

        Returns:

        """
        res: List[Dict[str, float]] = []
        if len(read_buf) <= 0:
            logging.warning('Empty record!!!')
            return res

        for idx in range(len(read_buf)):
            if read_buf[idx] == self.ADDR:
                _start_idx = idx
                _end_idx = _start_idx + 1 + struct.calcsize(self.ch_imu_data_t_fmt) + struct.calcsize(
                    self.hi229_dgram_meta_t_fmt)
                data_valid = self.verify_packet(read_buf[_start_idx: _end_idx], read_buf[_end_idx])
                if data_valid:
                    return {
                        "sync_start_idx": _start_idx,
                        "dgram_length": _end_idx - _start_idx + 1,
                        "imu_offset": 1,
                        "imu_length": struct.calcsize(self.ch_imu_data_t_fmt),
                        "imu_fmt": self.ch_imu_data_t_fmt,
                        "meta_offset": _start_idx + 1 + struct.calcsize(self.ch_imu_data_t_fmt),
                        "meta_length": struct.calcsize(self.hi229_dgram_meta_t_fmt),
                        "meta_fmt": self.hi229_dgram_meta_t_fmt
                    }
                else:
                    continue

            self.cursor += 1

        return None

    def _parse(self, read_buf, fmt) -> List[Dict]:
        result: List[Dict] = []
        start_idx = fmt['sync_start_idx']
        try:
            while start_idx + fmt['dgram_length'] < len(read_buf):
                imu_data = struct.unpack(
                    self.ch_imu_data_t_fmt,
                    read_buf[start_idx + fmt['imu_offset']:start_idx + fmt['imu_offset'] + fmt['imu_length']]
                )
                meta_data = struct.unpack(
                    self.hi229_dgram_meta_t_fmt,
                    read_buf[start_idx + fmt['meta_offset']:start_idx + fmt['meta_offset'] + fmt['meta_length']]
                )

                imu_dict: dict = {
                    "accel_x": imu_data[1], "accel_y": imu_data[2], "accel_z": imu_data[3],
                    "gyro_x": imu_data[4], "gyro_y": imu_data[5], "gyro_z": imu_data[6],
                    "roll": imu_data[10], "pitch": imu_data[11], "yaw": imu_data[12],
                    "quat_w": imu_data[13], "quat_x": imu_data[14], "quat_y": imu_data[15], "quat_z": imu_data[16],
                    "temp": 0.0,
                    "mag_x": imu_data[7], "mag_y": imu_data[8], "mag_z": imu_data[9],
                    "sys_ticks": imu_data[18]
                }

                meta_dict = {
                    'timestamp': meta_data[0],
                    'tsf_timestamp': meta_data[1],
                    'seq': meta_data[2],
                    'uart_buffer_len': meta_data[3],
                    'id': ''.join([chr(meta_data[4][idx]) for idx in range(len(meta_data[4]))]),
                }

                result.append({**imu_dict, **meta_dict})

                start_idx += fmt['dgram_length']
        except Exception as e:
            print(e)
            pass

        return result

    def __call__(self, f: BinaryIO) -> List[Dict[str, float]]:
        read_buf = f.read()
        if len(read_buf) <= 0:
            logging.warning("empty recording")
            return []
        fmt = self._sync(read_buf)
        result = self._parse(read_buf, fmt)

        return result


if __name__ == '__main__':
    parser = IMUParser()
    with open(
            r"C:\Users\liyutong\Desktop\rfimu-articulated-kit\imu_data\imu_mem_2022-10-25_233757/process_0_368.dat",
            'rb') as f:
        res = parser(f)

    print(res)
