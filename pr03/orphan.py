#!/usr/bin/env python3
"""Показывает усыновление сироты и завершает оба процесса."""

import os
import time
from pathlib import Path


def main() -> None:
    pid_file = Path(__file__).with_name("orphan.pid")
    pid = os.fork()

    if pid == 0:
        print(f"Ребёнок PID={os.getpid()}, начальный PPID={os.getppid()}", flush=True)
        time.sleep(1.5)
        print(f"Ребёнок PID={os.getpid()} после ухода родителя: PPID={os.getppid()}", flush=True)
        time.sleep(3)
        print(f"Ребёнок PID={os.getpid()} завершается", flush=True)
        os._exit(0)

    pid_file.write_text(str(pid), encoding="utf-8")
    print(f"Родитель PID={os.getpid()}, ребёнок PID={pid}", flush=True)
    time.sleep(0.5)
    print(f"Родитель PID={os.getpid()} завершается первым", flush=True)


if __name__ == "__main__":
    main()
