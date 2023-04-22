import multiprocessing as mp
import os.path as osp
from datetime import datetime

from rich.console import Console

from markit_gateway.functional import convert_measurement
from markit_gateway.config import BrokerConfig
from markit_gateway.tasks import measure


def main(option: BrokerConfig, tag: str):
    """start [measurement_name] - start measurement"""
    console = Console()
    console.print(f"Starting measurement, tag={tag}")

    signal_stop = mp.Event()
    signal_stop.clear()
    p = mp.Process(None,
                   measure,
                   "measure",
                   (
                       option,
                       tag,
                       signal_stop,
                   ), daemon=False)
    p.start()
    try:
        console.input("Press \\[enter] to stop measurement \n")
    except KeyboardInterrupt:
        pass

    signal_stop.set()
    p.join()

    # Convert
    try:
        convert_measurement(osp.join(option.base_dir, tag))
    except Exception as e:
        console.log(e, style="red")


if __name__ == '__main__':
    tag = 'imu_mem_' + datetime.now().strftime("%Y-%m-%d_%H%M%S")
    opt = BrokerConfig("imu_config.yaml")
    main(opt, tag)
