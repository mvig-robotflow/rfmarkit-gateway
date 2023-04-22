import multiprocessing as mp

from rich.console import Console

from markit_gateway.common import tcp_broadcast_command
from markit_gateway.config import BrokerConfig
from markit_gateway.utils import parse_cidr_addresses


def print_help():
    print("\
Commands: \n\
    > ping\n\
    > restart|shutdown\n\
    > update\n\
    > imu_cali_[reset|acc|mag]\n\
    > start|stop\n\
    > imu_[enable|disable|status|imm|setup|scale|debug]\n\
    > id\n\
    > ver\n\
    > time\n\
    > blink_[set|get|start|stop|off]\n\
    > v_{CONFIG_FIRMWARE_VERSION}_shutdown\n\
    > self_test \n\
    > always_on \n\
    > varget|varset\n\
    > probe* - probe client in a subnet\n\
    > quit* - quit this tool\n\n")


def control_from_keyboard(config: BrokerConfig,
                          client_info_queue: mp.Queue = None):
    # FIXME: Refactor this function to a cmd.Cmd based command line tool
    # FIXME: Track latest firmware version and update the command list
    imu_addresses = parse_cidr_addresses(config.imu_addresses)

    imu_port = config.imu_port

    console = Console()

    console.print(f"Welcome to Inertial Measurement Unit control system \n\n IMUs: \n")
    console.print(config.imu_addresses, imu_addresses)
    print_help()

    online_imus = set()
    try:
        while True:
            if client_info_queue is not None:
                while not client_info_queue.empty():
                    online_imus.add(str(client_info_queue.get()))

            if online_imus is not None:
                console.print(f"Online clients [{len(online_imus)}] :")
                console.print(online_imus)

            command = console.input("> ")
            if command == '':
                continue
            elif command in ['probe', 'p']:
                online_imus = [it['addr'] for it in tcp_broadcast_command(imu_addresses, imu_port, 'id', verbose=False)]
                continue
            elif command in ['quit', 'q']:
                break

            tcp_broadcast_command(online_imus, config.imu_port, command)

    except (KeyboardInterrupt, EOFError):
        print("Control Exiting")
        return


if __name__ == '__main__':
    control_from_keyboard(BrokerConfig('./config.json'))
