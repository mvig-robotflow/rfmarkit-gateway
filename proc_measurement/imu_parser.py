from io import FileIO
import numpy as np
import os
import time
import json
import datetime
from typing import List, Dict
import multiprocessing as mp
import tqdm
import logging
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
    "timestamp": [32, 40],
    "id": [40, 52],
    "data": [0, 32]
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

def extract_meta(data):
    """Extract meta info from data

    Args:
        data ([type]): [description]
    """
    timestamp: float = sum([data[idx] * 0x100**(idx - META_FORMAT["timestamp"][0]) for idx in range(*META_FORMAT["timestamp"])])  / 1e6
    device_id: str = ''.join([chr(data[idx]) for idx in range(*META_FORMAT["id"])])
    return timestamp, device_id

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
    for key in res.keys():
        value = data[DATA_FORMAT[key][0]] * 256 + data[DATA_FORMAT[key][1]]
        value = -(65536 - value) if value >= 32768 else value
        res[key] = value * DATA_DIVIDER[key]
    
    res["timestamp"], res["id"] = extract_meta(data)
    return res

class IMUParser:
    ADDR = 0xa4
    READ_OP = 0x03
    REG_THRESH = 0x2c
    DEFAULT_START_REG = 0x14
    BLOCK_SZ: int = 0x1000

    def __init__(self) -> None:
        self.buf: np.ndarray = np.zeros(shape=(60), dtype=np.uint8)
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
    def _parse(self, read_buf: bytearray):
        res: List[Dict[str, float]] = []
        if len(read_buf) <= 0:
            # TODO: Think about what we should do with an empty file
            return res 

        for idx in range(len(read_buf)):
            self.buf[self.cursor] = read_buf[idx]

            if self.cursor == 0:
                if self.buf[0] != self.ADDR:
                    self._reset()
                    continue
            elif self.cursor == 1:
                if self.buf[1] != self.READ_OP:
                    self._reset()
                    continue

            elif self.cursor == 2:
                if self.buf[2] < self.REG_THRESH:
                    self.start_reg = self.buf[2]
                else:
                    self._reset()
                    continue

            elif self.cursor == 3:
                if self.start_reg + self.buf[3] < self.REG_THRESH:
                    self.length = self.buf[3]
                else:
                    self._reset()
                    continue

            elif self.length + 5 == self.cursor: # Magic Number 5: 1(addr) + 1(read_op) + 1(start_reg) + 1(end_reg) + 1(chksum)
                # Received a complete datagram
                self.data_valid = sum(self.buf[:self.cursor - 1]) % 0x100 == self.buf[self.cursor - 1]
            
            elif self.length + 26 == self.cursor: # Magic Number 26 5 + 8(timestamp) + 12(id) + 1(chksum)
                self.meta_valid = sum(self.buf[:self.cursor - 1]) % 0x100 == self.buf[self.cursor - 1]
                # Apply parse function if both field is valid
                if self.meta_valid and self.data_valid:
                    res.append(parse_data(self.buf))
                else:
                    # Reset flags
                    logging.warn(f"Flags are not valid: data={self.data_valid}, meta={self.meta_valid}")
                self._reset()
                continue

            self.cursor += 1
        
        return res

    def __call__(self, f: FileIO) -> List[Dict[str, float]]:
        read_buf = f.read() # TODO: Here we read all to memory, might fail in limited memory settings
        res = self._parse(read_buf)
        return res


if __name__ == '__main__':
    gy = IMUParser()
    with open('/home/liyutong/Tasks/imu-node-deploy/tcp_broker/imu_data/imu_mem_2021-11-02_010812/process_0_29.dat', 'rb') as f:
        res = gy(f)

    print(res)