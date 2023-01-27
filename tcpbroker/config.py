import multiprocessing as mp
from typing import Dict, Any, List

import yaml
from py_cli_interaction import must_parse_cli_int, must_parse_cli_string, must_parse_cli_bool, must_parse_cli_float


class BrokerConfig:
    __DEFAULT_N_PROCS__: int = min(4, mp.cpu_count())
    __DEFAULT_DATA_DIR__: str = './imu_data'
    __DEFAULT_TCP_BUFF_SZ__: int = 1024
    __DEFAULT_API_PORT__: int = 18889
    __DEFAULT_IMU_PORT__: int = 18888
    __DEFAULT_DATA_PORT__: int = 18888
    __DEFAULT_DATA_ADDR__: str = "0.0.0.0"
    __DEFAULT_ENABLE_GUI__: bool = False
    __DEFAULT_RENDER_PACKET__: bool = True
    __DEFAULT_UPDATE_INTERVAL_S__: float = 1e-1
    __DEFAULT_DEBUG__: bool = False

    n_procs: int = __DEFAULT_N_PROCS__
    base_dir: str = __DEFAULT_DATA_DIR__
    tcp_buff_sz: int = __DEFAULT_TCP_BUFF_SZ__
    api_port: int = __DEFAULT_API_PORT__
    imu_port: int = __DEFAULT_IMU_PORT__
    data_port: int = __DEFAULT_DATA_PORT__
    data_addr: str = __DEFAULT_DATA_ADDR__
    enable_gui: bool = __DEFAULT_ENABLE_GUI__
    render_packet: bool = __DEFAULT_RENDER_PACKET__
    update_interval_s: float = __DEFAULT_UPDATE_INTERVAL_S__
    debug: bool = __DEFAULT_DEBUG__

    imu_addresses: List[str] = []

    def __init__(self, path_to_yaml_file: str = None):
        if path_to_yaml_file is not None:
            with open(path_to_yaml_file) as f:
                base_cfg_dict = yaml.load(f, Loader=yaml.SafeLoader)
            self.load_dict(base_cfg_dict['imu'])
        else:
            self.__post_init__()

    def __repr__(self):
        return f"<BrokerConfig: data_dir={self.base_dir}, api_port={self.api_port}>"

    def __post_init__(self):
        if self.imu_addresses is None:
            self.imu_addresses = []

    def load_dict(self, src: Dict[str, Any]) -> None:
        self.n_procs = src['n_procs']
        self.base_dir = src['base_dir']
        self.tcp_buff_sz = src['tcp_buff_sz']
        self.api_port: int = src['api_port']
        self.imu_port: int = src['imu_port']
        self.data_port: int = src['data_port']
        self.data_addr: str = src['data_addr']
        self.enable_gui: bool = src['enable_gui']
        self.render_packet: bool = src['render_packet']
        self.update_interval_s: float = src['update_interval_s']
        self.imu_addresses = src['imu_addresses']
        self.debug = src['debug']
        self.__post_init__()

    def get_dict(self) -> Dict[str, Any]:
        return {
            'n_procs': self.n_procs,
            'base_dir': self.base_dir,
            'tcp_buff_sz': self.tcp_buff_sz,
            'api_port': self.api_port,
            'imu_port': self.imu_port,
            'data_port': self.data_port,
            'data_addr': self.data_addr,
            'enable_gui': self.enable_gui,
            'render_packet': self.render_packet,
            'update_interval_s': self.update_interval_s,
            'imu_addresses': self.imu_addresses,
            'debug': self.debug
        }

    def configure_from_keyboard(self):
        self.n_procs = must_parse_cli_int("Number of processes?", min=1, max=13, default_value=self.__DEFAULT_N_PROCS__)
        self.base_dir = must_parse_cli_string("Data directory?", default_value=self.__DEFAULT_DATA_DIR__)
        self.tcp_buff_sz = must_parse_cli_int("TCP buffer size?", min=1024, max=10241, default_value=self.__DEFAULT_TCP_BUFF_SZ__)
        self.api_port = must_parse_cli_int("API port?", min=18889, max=65536, default_value=self.__DEFAULT_API_PORT__)
        self.imu_port = must_parse_cli_int("IMU port?", default_value=self.__DEFAULT_IMU_PORT__)
        self.data_port = must_parse_cli_int("Data port?", default_value=self.__DEFAULT_IMU_PORT__)
        self.data_addr = must_parse_cli_string("Data address?", default_value=self.__DEFAULT_DATA_ADDR__)
        self.enable_gui = must_parse_cli_bool("Enable GUI?", default_value=False)
        self.render_packet = must_parse_cli_bool("Render packet?", default_value=True)
        self.update_interval_s = must_parse_cli_float("Update interval (s)?", min=1e-3, max=1e3, default_value=self.__DEFAULT_UPDATE_INTERVAL_S__)
        self.debug = must_parse_cli_bool("Debug?", default_value=False)
