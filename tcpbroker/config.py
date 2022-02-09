import multiprocessing as mp
import os

# Constants
TCP_BUFF_SZ: int = 1024
POLL_TIMEOUT_MS: int = 1000

# Runtime variable from environment
DEBUG: bool = 'DEBUG' in os.environ.keys()
# N_PROC: int = 1
# N_PROC: int = mp.cpu_count()
N_PROC = int(os.environ['N_PROC']) if 'N_PROC' in os.environ.keys() else min(4, mp.cpu_count())
DATA_DIR: str = os.environ['DATA_DIR'] if 'DATA_DIR' in os.environ.keys() else './imu_data'
