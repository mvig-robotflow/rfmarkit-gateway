import socket
import multiprocessing as mp
import argparse

TCP_BUFF_SZ: int = 1024
DEBUG: bool = True
idx: int = 0

def tcp_process_task(client_socket: socket.socket):
    global idx
    while True:
        data = client_socket.recv(TCP_BUFF_SZ)
        if len(data) <= 0:
            print("[ Info ] Client disconnected")
            break
        if len(data) > 0:
            pass
            print(f"Idx: {idx}; Data len:{len(data)}")
            print(data)
            idx += 1
            
    client_socket.close()
    return

def test(address: str, port: int, max_listen: int=64) -> None:
    server_socket:socket.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((address, port))
    server_socket.listen(max_listen)
    print("[ Info ] Binding address {}:{}".format(address, port))
    client_procs = []
    try:
        while True:
            client_socket, (client_address, client_port) = server_socket.accept()
            print("[ Info ] New client {}:{}".format(client_address, client_port))
            client_proc = mp.Process(None, tcp_process_task, "tcp_process_{}:{}".format(client_address, client_port), (client_socket, ))
            client_proc.start()
            client_procs.append(client_proc)
    except KeyboardInterrupt:
        print("Exitting")
        for proc in client_procs:
            proc.join()
        return


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int, default=18889)
    args = parser.parse_args()

    test('0.0.0.0', args.port)