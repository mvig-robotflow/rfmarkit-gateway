import socket
import time
import json
from datetime import datetime
import uuid
import random

ID = str(uuid.uuid1())[:12]
# {"id":"84f7033b3e78","timestamp":1634821243683675,}

HOST: str = "127.0.0.1"
IMU_PORT: int = 18888
if __name__ == '__main__':
    client_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    while True:
        try:
            client_sock.connect((HOST, IMU_PORT))
            break
        except Exception:
            continue

    try:
        while True:
            time.sleep(0.01)
            DUMMY_MSG = json.dumps({"id": ID, 
                                    "timestamp": time.mktime(datetime.utcnow().timetuple()), 
                                    "accel_x":-769,"accel_y":512,"accel_z":1008,"gyro_x":256,"gyro_y":-1,"gyro_z":0,"roll":1024,"pitch":-1025,"yaw":6167,"temp":-5108,"mag_x":-8188,"mag_y":770,"mag_z":4091,
                                    "data": random.randint(0,4096)}) + '\n'
            client_sock.send(bytes(DUMMY_MSG, encoding='ascii'))
    except KeyboardInterrupt:
        client_sock.close()

