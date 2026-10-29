#!/usr/bin/env python3
"""Параллельный сервер выражений на Unix domain socket."""

import argparse
import socket
import threading
from common import IPC_DIR, SOCKET_PATH, answer

print_lock = threading.Lock()


def handle(connection: socket.socket, expression_number: int) -> None:
    with connection:
        data = b""
        while not data.endswith(b"\n"):
            chunk = connection.recv(4096)
            if not chunk:
                break
            data += chunk
        expression = data.decode("utf-8").strip()
        connection.sendall((answer(expression) + "\n").encode("utf-8"))
    with print_lock:
        print(f"Клиент {expression_number}: {expression}", flush=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--clients", type=int, default=1)
    args = parser.parse_args()
    IPC_DIR.mkdir(exist_ok=True)
    SOCKET_PATH.unlink(missing_ok=True)
    threads = []
    try:
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as server:
            server.bind(str(SOCKET_PATH))
            server.listen(args.clients)
            print(f"Socket-сервер готов, ожидает клиентов: {args.clients}", flush=True)
            for number in range(1, args.clients + 1):
                connection, _ = server.accept()
                thread = threading.Thread(target=handle, args=(connection, number))
                thread.start()
                threads.append(thread)
            for thread in threads:
                thread.join()
    finally:
        SOCKET_PATH.unlink(missing_ok=True)
        try:
            IPC_DIR.rmdir()
        except OSError:
            pass


if __name__ == "__main__":
    main()
