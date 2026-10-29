#!/usr/bin/env python3
"""Временно создаёт zombie, затем родитель обязательно вызывает waitpid."""

import os
import time
from pathlib import Path


def child_state(pid: int) -> str:
    try:
        for line in Path(f"/proc/{pid}/status").read_text(encoding="utf-8").splitlines():
            if line.startswith("State:"):
                return line.split(":", 1)[1].strip()
    except FileNotFoundError:
        return "процесс уже убран"
    return "неизвестно"


def main() -> None:
    pid = os.fork()
    if pid == 0:
        os._exit(0)

    print(f"Родитель PID={os.getpid()}, ребёнок PID={pid}", flush=True)
    print("Ребёнок завершается, но родитель пока не вызывает waitpid...", flush=True)
    time.sleep(1)
    print(f"Состояние ребёнка до waitpid: {child_state(pid)}", flush=True)
    time.sleep(3)
    os.waitpid(pid, 0)
    print(f"Состояние после waitpid: {child_state(pid)}", flush=True)


if __name__ == "__main__":
    main()
