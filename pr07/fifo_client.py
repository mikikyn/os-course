#!/usr/bin/env python3
"""Клиент FIFO: отправляет выражение и читает ответ через второй FIFO."""

import argparse
from common import REQUEST_FIFO, RESPONSE_FIFO


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("expression")
    args = parser.parse_args()
    with REQUEST_FIFO.open("w", encoding="utf-8") as request:
        request.write(args.expression + "\n")
    with RESPONSE_FIFO.open("r", encoding="utf-8") as response:
        result = response.readline().strip()
    print(f"{args.expression} = {result}")


if __name__ == "__main__":
    main()
