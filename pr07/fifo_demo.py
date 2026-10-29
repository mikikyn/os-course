#!/usr/bin/env python3
"""Автоматический запуск FIFO-сервера и трёх клиентов по очереди."""

import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).parent


def main() -> None:
    start = time.perf_counter()
    server = subprocess.Popen(
        [sys.executable, str(ROOT / "fifo_server.py"), "--clients", "3"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    try:
        time.sleep(0.15)
        expected = {"2 + 3 * 4": "14", "(10 - 4) / 2": "3.0", "-5 + 8": "3"}
        for expression, wanted in expected.items():
            result = subprocess.run(
                [sys.executable, str(ROOT / "fifo_client.py"), expression],
                check=True,
                capture_output=True,
                text=True,
                timeout=10,
            )
            print(result.stdout.strip())
            if not result.stdout.strip().endswith("= " + wanted):
                raise AssertionError(f"Неверный ответ для {expression}")
        server.wait(timeout=10)
        print(server.communicate()[0].strip())
    finally:
        if server.poll() is None:
            server.terminate()
            server.wait()
    print(f"FIFO: 3 последовательных клиента, время={time.perf_counter() - start:.4f} с; FIFO удалены")


if __name__ == "__main__":
    main()
