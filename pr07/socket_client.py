#!/usr/bin/env python3
"""Клиент Unix domain socket."""

import argparse
import socket
from common import SOCKET_PATH


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("expression")
    args = parser.parse_args()
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as client:
        client.connect(str(SOCKET_PATH))
        client.sendall((args.expression + "\n").encode("utf-8"))
        data = b""
        while not data.endswith(b"\n"):
            chunk = client.recv(4096)
            if not chunk:
                break
            data += chunk
    print(f"{args.expression} = {data.decode('utf-8').strip()}")


if __name__ == "__main__":
    main()
