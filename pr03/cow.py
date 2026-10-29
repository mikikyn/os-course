#!/usr/bin/env python3
"""Демонстрирует copy-on-write после fork по RSS и smaps_rollup."""

import os
from pathlib import Path


def memory_values(pid: int) -> dict[str, int]:
    result = {"VmRSS": 0, "Shared_Dirty": 0, "Private_Dirty": 0}
    try:
        for line in Path(f"/proc/{pid}/status").read_text(encoding="utf-8").splitlines():
            if line.startswith("VmRSS:"):
                result["VmRSS"] = int(line.split()[1])
        for line in Path(f"/proc/{pid}/smaps_rollup").read_text(encoding="utf-8").splitlines():
            key = line.split(":", 1)[0]
            if key in ("Shared_Dirty", "Private_Dirty"):
                result[key] = int(line.split()[1])
    except (FileNotFoundError, PermissionError):
        pass
    return result


def print_memory(label: str, pid: int) -> None:
    values = memory_values(pid)
    print(
        f"{label}: VmRSS={values['VmRSS']} kB, "
        f"Shared_Dirty={values['Shared_Dirty']} kB, "
        f"Private_Dirty={values['Private_Dirty']} kB",
        flush=True,
    )


def main() -> None:
    data = list(range(1_000_000))
    print(f"Родитель PID={os.getpid()} создал список из {len(data)} чисел", flush=True)
    pid = os.fork()

    if pid == 0:
        child_pid = os.getpid()
        print_memory("Ребёнок до изменения", child_pid)
        for index in range(len(data)):
            data[index] += 1
        print_memory("Ребёнок после изменения", child_pid)
        print(f"Контрольная сумма ребёнка: {sum(data)}", flush=True)
        os._exit(0)

    os.waitpid(pid, 0)
    print_memory("Родитель после завершения ребёнка", os.getpid())
    print(f"Контрольная сумма родителя: {sum(data)}", flush=True)
    print("Списки различаются: ребёнок изменил свою копию, родитель — нет.", flush=True)


if __name__ == "__main__":
    main()
