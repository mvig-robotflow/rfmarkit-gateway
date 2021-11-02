import socket
import asyncio
import logging
logging.basicConfig(level=logging.INFO)

from typing import List

async def udp_send_bytes(sock: socket.socket, addr: str, port: int, data:bytes, n_repeat: int = 1):
    logging.info(f"Sending {data} to {addr}:{port} for {n_repeat} times")

    for _ in range(n_repeat):
        server_address = (addr, port)
        sock.sendto(data, server_address)
        reply = ''
        # try:
        #     while True:
        #         reply += str(sock.recv(1024), encoding='ascii')
        # except socket.timeout:
        #     logging.warn("Socket timeout")
    return reply

def gen_ip_address(subnet: List[int]): # TODO: Only support *.*.*.0/24
    postfix = subnet[-1]
    while postfix < 256:
        yield ".".join(map(lambda x: str(x),subnet[:3])) + '.' + str(postfix)
        postfix += 1

async def control(port: int):
    # Setup the server
    ctrl_socket: socket.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    # ctrl_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    ctrl_socket.settimeout(5) # TODO: Magic timeout

    # Get subnet, like [10,52,24,0]
    try:
        subnet: List[int] = list(map(lambda x: int(x), input("Input subnet of IMUs, e.g. 10.52.24.0\n> ").split(".")))
    except ValueError:
        logging.info("Wrong input, use default value(10.52.24.0)")
        subnet = [10,52,24,0]

    print(f"Welcome to Inertial Measurement Unit control system \n\nSending to {subnet}\nCommands: \n    > restart\n    > ping\n    > sleep\n    > shutdown\n    > update\n    > cali_reset\n    > cali_acc\n    > cali_mag\n    > start\n    > stop\n\n    > quit - quit this tool\n")
    n_repeat: int = 1
    try:
        while True:
            command = input("> ")
            if command in ['quit', 'q']:
                break

            # Usually 3 repeats will guarantee
            if command in ['start', 'stop', 'shutdown', 'restart', 'update']:
                n_repeat = 3
            else:
                n_repeat = 1

            results_list = await asyncio.gather(*[udp_send_bytes(ctrl_socket, addr, port, bytes(command, encoding='ascii'), n_repeat) for addr in gen_ip_address(subnet)])
            # print(list(filter(lambda x: len(x) > 0, results_list)))
            # reply = await udp_send_bytes(ctrl_socket, ".".join(map(lambda x:str(x),subnet[:3])) + ".255", port, bytes(command, encoding='ascii'))
            # logging.info(reply)
            print("\nCommands: \n    > restart\n    > ping\n    > sleep\n    > shutdown\n    > update\n    > cali_reset\n    > cali_acc\n    > cali_mag\n    > start\n    > stop\n\n    > quit - quit this tool\n")
    except KeyboardInterrupt:
        print("Exitting")
        return

if __name__ == '__main__':
    asyncio.run(control(18888))





