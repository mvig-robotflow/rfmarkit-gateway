import multiprocessing as mp
import select
import os

OSS_ENDPOINT = os.getenv('OSS_ENDPOINT')
OSS_BUCKET = os.getenv('OSS_BUCKET')
OSS_ACCESSKEY = os.getenv('OSS_ACCESSKEY')
OSS_SECRETKEY = os.getenv('OSS_SECRETKEY')
PROCESSOR_APIHOST = os.getenv('PROCESSOR_APIHOST')

assert(OSS_ENDPOINT is not None), AssertionError("OSS_ENDPOINT not found in environment")
assert(OSS_BUCKET is not None), AssertionError("OSS_BUCKET not found in environment")
assert(OSS_ACCESSKEY is not None), AssertionError("OSS_ACCESSKEY not found in environment")
assert(OSS_SECRETKEY is not None), AssertionError("OSS_SECRETKEY not found in environment")

# Constants
TCP_BUFF_SZ: int = 1024
POLL_READ = select.POLLIN | select.POLLPRI | select.POLLHUP | select.POLLERR
POLL_TIMEOUT_MS: int = 1000

# Runtime variable from environment
DEBUG: bool = 'DEBUG' in os.environ.keys()
# N_PROC: int = mp.cpu_count()
N_PROC = int(os.environ['N_PROC']) if 'N_PROC' in os.environ.keys() else mp.cpu_count()
DATA_DIR: str = os.environ['DATA_DIR'] if 'DATA_DIR' in os.environ.keys() else './imu_data'