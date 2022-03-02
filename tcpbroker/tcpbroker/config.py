import json
import multiprocessing as mp
import os


class BrokerConfig:
    def __init__(self, configuration_path: str):

        if os.path.exists(configuration_path):
            with open(configuration_path, 'r') as f:
                try:
                    CONFIG = json.load(f)
                except:
                    CONFIG = None
        else:
            CONFIG = None

        self.DEFAULT_SUBNET = CONFIG['default_subnet'] if CONFIG is not None and "default_subnet" in CONFIG.keys() and isinstance(CONFIG["default_subnet"], str) else None
        self.N_PROCS = CONFIG['n_procs'] if CONFIG is not None and "n_procs" in CONFIG.keys() and isinstance(CONFIG["n_procs"], int) else min(4, mp.cpu_count())
        self.DATA_DIR = CONFIG['data_dir'] if CONFIG is not None and "data_dir" in CONFIG.keys() and isinstance(CONFIG["data_dir"], str) else './imu_data'
        self.TCP_BUFF_SZ = CONFIG['tcp_buff_sz'] if CONFIG is not None and "tcp_buff_sz" in CONFIG.keys() and isinstance(CONFIG["tcp_buff_sz"], int) else 1024
        self.API_PORT: int = CONFIG['api_port'] if CONFIG is not None and "api_port" in CONFIG.keys() and isinstance(CONFIG["api_port"], int) else 5051
        self.DEBUG = 'DEBUG' in os.environ.keys()
