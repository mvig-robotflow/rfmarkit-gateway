import logging

from py_cli_interaction import must_parse_cli_sel
from rich.console import Console

from markit_gateway.common import tcp_broadcast_command
from markit_gateway.config import BrokerConfig
from markit_gateway.utils import parse_cidr_addresses


def easy_setup(config: BrokerConfig):
    _logger = logging.getLogger("easy_setup")
    console = Console()
    imu_addresses = parse_cidr_addresses(config.imu_addresses)
    imu_port = config.imu_port

    _logger.debug(imu_addresses)
    _logger.debug(imu_port)

    try:
        while True:
            sel: int = must_parse_cli_sel("请选择操作：",
                                          [
                                              "查看在线传感器情况",
                                              "启动传感器",
                                              "停止传感器",
                                              "重置传感器",
                                              "退出"
                                          ],
                                          1, 5)

            if sel == 1:
                tcp_broadcast_command(imu_addresses, imu_port, "ping", True)
            elif sel == 2:
                tcp_broadcast_command(imu_addresses, imu_port, "start", True)
            elif sel == 3:
                tcp_broadcast_command(imu_addresses, imu_port, "stop", True)
            elif sel == 4:
                tcp_broadcast_command(imu_addresses, imu_port, "restart", True)
            elif sel == 5:
                break
            else:
                print("\n错误的输入\n")

            # print_help()
    except (KeyboardInterrupt, EOFError):
        pass
    finally:
        console.log("easy_setup Exiting")
        return


if __name__ == '__main__':
    easy_setup(BrokerConfig())
