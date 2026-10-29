#!/usr/bin/env python3
"""Запускает N дочерних процессов через fork + exec и ждёт каждый."""

import os
import sys
import time


def main() -> None:
    if len(sys.argv) < 3:
        print(f"Использование: python3 {sys.argv[0]} N КОМАНДА [АРГУМЕНТЫ...]", file=sys.stderr)
        sys.exit(1)

    try:
        count = int(sys.argv[1])
        if count < 1:
            raise ValueError
    except ValueError:
        print("N должно быть положительным целым числом.", file=sys.stderr)
        sys.exit(1)

    command = sys.argv[2:]
    started: dict[int, float] = {}

    for _ in range(count):
        start = time.monotonic()
        pid = os.fork()
        if pid == 0:
            try:
                os.execvp(command[0], command)
            except OSError as error:
                print(f"exec не удался: {error}", file=sys.stderr, flush=True)
                os._exit(127)
        started[pid] = start

    print(f"Родитель PID={os.getpid()} создал {count} процессов: {', '.join(map(str, started))}", flush=True)

    for pid in started:
        waited_pid, status = os.waitpid(pid, 0)
        elapsed = time.monotonic() - started[pid]
        if os.WIFEXITED(status):
            result = f"код={os.WEXITSTATUS(status)}"
        elif os.WIFSIGNALED(status):
            result = f"сигнал={os.WTERMSIG(status)}"
        else:
            result = f"статус={status}"
        print(f"PID={waited_pid} завершился: {result}, время={elapsed:.3f} с")


if __name__ == "__main__":
    main()
