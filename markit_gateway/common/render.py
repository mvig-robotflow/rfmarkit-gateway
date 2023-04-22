import logging
import multiprocessing as mp
import struct
import time
from io import BytesIO
from typing import Dict, List, Tuple, Optional, BinaryIO, Union
import numpy as np


class IMURender:
    ch_imu_data_t_fmt = "I3f3f3f3f4ffI"
    imu_packet_length = struct.calcsize(ch_imu_data_t_fmt)
    dgram_meta_t_fmt = "=qqIi12s"
    meta_packet_length = struct.calcsize(dgram_meta_t_fmt)
    imu_addr: bytes = b'\xe5'
    addr_length = 1
    packet_length = addr_length + \
                    struct.calcsize(ch_imu_data_t_fmt) + struct.calcsize(dgram_meta_t_fmt)

    buffer: BytesIO = BytesIO()

    filename: Optional[str] = None
    file_handle: Optional[BinaryIO] = None
    out_queue: Optional[mp.Queue] = None
    update_interval_s: Optional[float] = None
    last_update_time: Optional[float] = None

    state: Optional[Dict[str, Union[float, str, int]]] = None
    state_is_valid: bool = False

    def __init__(self,
                 filename: str = None,
                 update_interval_s: float = 1e-1,
                 out_queue: mp.Queue = None):
        self.filename = filename
        if self.filename is not None:
            self.file_handle = open(self.filename, "ab")

        self.out_queue = out_queue
        self.update_interval_s = update_interval_s
        self.last_update_time = time.time()

    @staticmethod
    def verify_packet(buf, chksum: int) -> bool:
        arr = np.frombuffer(buf, dtype=np.uint8)
        arr_chksum = np.bitwise_xor.reduce(arr)
        return arr_chksum == chksum

    def _parse_packet(self, pkt: bytes) -> Dict[str, Union[float, str, int]]:
        imu_struct = struct.unpack(self.ch_imu_data_t_fmt,
                                   pkt[self.addr_length:self.addr_length + self.imu_packet_length])
        meta_struct = struct.unpack(
            self.dgram_meta_t_fmt, pkt[self.addr_length + self.imu_packet_length:])

        imu_dict: dict = {
            "accel_x": imu_struct[1], "accel_y": imu_struct[2], "accel_z": imu_struct[3],
            "gyro_x": imu_struct[4], "gyro_y": imu_struct[5], "gyro_z": imu_struct[6],
            "roll": imu_struct[10], "pitch": imu_struct[11], "yaw": imu_struct[12],
            "quat_w": imu_struct[13], "quat_x": imu_struct[14], "quat_y": imu_struct[15],
            "quat_z": imu_struct[16],
            "temp": 0.0,
            "mag_x": imu_struct[7], "mag_y": imu_struct[8], "mag_z": imu_struct[9],
            "sys_ticks": imu_struct[18]
        }

        meta_dict = {
            'timestamp': meta_struct[0],
            'tsf_timestamp': meta_struct[1],
            'seq': meta_struct[2],
            'uart_buffer_len': meta_struct[3],
            'id': ''.join([chr(meta_struct[4][idx]) for idx in range(len(meta_struct[4]))]),
        }
        return {**imu_dict, **meta_dict}

    def _try_sync(self, data: bytes) -> Tuple[bool, List[Dict[str, Union[float, str, int]]]]:

        self.buffer.write(data)
        self.buffer.seek(0)

        while (addr := self.buffer.read(1)) != self.imu_addr:
            if addr == b'':
                return False, []
        self.buffer.seek(self.buffer.tell() - 1)

        _content = self.buffer.read(self.packet_length)
        _chksum = self.buffer.read(1)
        if len(_content) < self.packet_length or len(_chksum) < 1:
            self.buffer.write(_content)
            self.buffer.write(_chksum)
            return False, []

        data_valid = self.verify_packet(_content, int(_chksum[0]))

        if data_valid:
            self.buffer.seek(self.buffer.tell() - self.packet_length - 1)
            res = []
            while True:
                pkt = self.buffer.read(self.packet_length)
                checksum = self.buffer.read(1)
                if len(pkt) < self.packet_length or checksum == b'':
                    self.buffer = BytesIO(pkt)
                    self.buffer.read()  # move pointer to end using read
                    break
                res.append(self._parse_packet(pkt))
            return True, res
        else:
            return False, []

    def update(self, data: bytes):
        # If not synced, try to sync
        success, res = self._try_sync(data)
        if success:
            self.state_is_valid = True
            self.state = res[-1]
            # Communicate
            if self.out_queue is not None and not self.out_queue.full():
                try:
                    time_elapsed = time.time() - self.last_update_time
                    if time_elapsed > self.update_interval_s:
                        self.out_queue.put(self.state, timeout=1)
                        self.last_update_time = time.time()
                except TimeoutError as _:  # ignore timeout error
                    pass
        else:
            self.state_is_valid = False

        # Flush data to disk
        if self.file_handle is not None:
            self.file_handle.write(data)

        return res

    def submit_buffer(self, data: bytes):
        _, res = self._try_sync(data)
        return res

    def close(self):
        self.file_handle.close()


# States:
# - Captured IMU.addr e5, Not Synced
# - %
if __name__ == '__main__':
    logging.info('start')
    imu_data = open(
        r"C:\Users\liyutong\Desktop\rfimu-articulated-kit\imu_data\imu_mem_2022-10-25_233757\process_0_368.dat",
        "rb").read()
    print(len(imu_data))
    obj = IMURender()

    piece1 = imu_data[:500]
    s_t = time.time()
    print(obj.update(piece1))
    print(time.time() - s_t)

    piece2 = imu_data[500:1000]
    s_t = time.time()
    print(obj.update(piece2))
    print(time.time() - s_t)

    piece2 = imu_data[1000:5096]
    s_t = time.time()
    print(obj.update(piece2))
    print(time.time() - s_t)
