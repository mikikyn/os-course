#!/usr/bin/env python3
"""Запускает шесть одновременных клиентов Unix-сокета отдельными процессами."""

import subprocess
import sys
import time
from pathlib import Path
from common import SOCKET_PATH

ROOT = Path(__file__).parent


def main() -> None:
    start = time.perf_counter()
    server = subprocess.Popen(
        [sys.executable, str(ROOT / "socket_server.py"), "--clients", "6"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    clients = []
    try:
        for _ in range(100):
            if SOCKET_PATH.exists():
                break
            time.sleep(0.03)
        else:
            raise RuntimeError("Сокет не появился")

        for index in range(6):
            expression = f"{index + 1} * 10 + 2"
            client = subprocess.Popen(
                [sys.executable, str(ROOT / "socket_client.py"), expression],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
            )
            clients.append((index, expression, client))
        for index, expression, client in clients:
            output = client.communicate(timeout=10)[0].strip()
            if client.returncode != 0 or not output.endswith(f"= {(index + 1) * 10 + 2}"):
                raise AssertionError(output)
            print(output)
        server.wait(timeout=10)
        print(server.communicate()[0].strip())
    finally:
        for _, _, client in clients:
            if client.poll() is None:
                client.terminate()
                client.wait()
        if server.poll() is None:
            server.terminate()
            server.wait()
    print(f"Unix socket: 6 одновременных клиентов, время={time.perf_counter() - start:.4f} с; сокет удалён")


if __name__ == "__main__":
    main()
