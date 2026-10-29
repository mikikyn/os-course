#!/usr/bin/env python3
"""Сервер выражений на двух именованных каналах FIFO."""

import argparse
import os
from common import IPC_DIR, REQUEST_FIFO, RESPONSE_FIFO, answer


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--clients", type=int, default=1)
    args = parser.parse_args()
    IPC_DIR.mkdir(exist_ok=True)
    REQUEST_FIFO.unlink(missing_ok=True)
    RESPONSE_FIFO.unlink(missing_ok=True)
    os.mkfifo(REQUEST_FIFO, 0o600)
    os.mkfifo(RESPONSE_FIFO, 0o600)
    print(f"FIFO-сервер готов, ожидает клиентов: {args.clients}", flush=True)
    try:
        for _ in range(args.clients):
            with REQUEST_FIFO.open("r", encoding="utf-8") as request:
                expression = request.readline().strip()
            with RESPONSE_FIFO.open("w", encoding="utf-8") as response:
                response.write(answer(expression) + "\n")
            print(f"Обработано: {expression}", flush=True)
    finally:
        REQUEST_FIFO.unlink(missing_ok=True)
        RESPONSE_FIFO.unlink(missing_ok=True)
        try:
            IPC_DIR.rmdir()
        except OSError:
            pass


if __name__ == "__main__":
    main()
