#!/usr/bin/env python3
"""Полный алгоритм банкира: safety и запросы с откатом."""

import re
import sys
from pathlib import Path


def pid_key(pid: str) -> tuple[int, str]:
    match = re.search(r"\d+", pid)
    return int(match.group()) if match else 10**9, pid


class Banker:
    def __init__(self, available, allocation, maximum):
        self.available = list(available)
        self.allocation = {pid: list(values) for pid, values in allocation.items()}
        self.maximum = {pid: list(values) for pid, values in maximum.items()}

    def need(self, pid: str) -> list[int]:
        return [maximum - allocated for maximum, allocated in zip(self.maximum[pid], self.allocation[pid])]

    def safety(self):
        work = self.available.copy()
        finished = set()
        sequence = []
        pids = sorted(self.allocation, key=pid_key)
        cursor = 0

        while len(finished) < len(pids):
            for offset in range(len(pids)):
                index = (cursor + offset) % len(pids)
                pid = pids[index]
                if pid in finished:
                    continue
                if all(need <= available for need, available in zip(self.need(pid), work)):
                    work = [
                        available + allocated
                        for available, allocated in zip(work, self.allocation[pid])
                    ]
                    finished.add(pid)
                    sequence.append(pid)
                    cursor = (index + 1) % len(pids)
                    break
            else:
                return False, []
        return True, sequence

    def request(self, pid: str, vector) -> bool:
        if pid not in self.allocation or len(vector) != len(self.available):
            return False
        if any(value < 0 for value in vector):
            return False
        if any(requested > needed for requested, needed in zip(vector, self.need(pid))):
            return False
        if any(requested > available for requested, available in zip(vector, self.available)):
            return False

        old_available = self.available.copy()
        old_allocation = self.allocation[pid].copy()
        self.available = [available - requested for available, requested in zip(self.available, vector)]
        self.allocation[pid] = [allocated + requested for allocated, requested in zip(self.allocation[pid], vector)]
        safe, _ = self.safety()
        if safe:
            return True
        self.available = old_available
        self.allocation[pid] = old_allocation
        return False


def load(path: str | Path) -> Banker:
    available = None
    allocation = {}
    maximum = {}
    for raw in Path(path).read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split()
        if parts[0] == "AVAILABLE":
            available = [int(value) for value in parts[1:]]
            continue
        if len(parts) != 7:
            raise ValueError(f"Некорректная строка: {line}")
        pid = parts[0]
        values = [int(value) for value in parts[1:]]
        allocation[pid] = values[:3]
        maximum[pid] = values[3:]
    if available is None or len(available) != 3:
        raise ValueError("Нужна строка AVAILABLE с тремя ресурсами")
    return Banker(available, allocation, maximum)


def main() -> None:
    if len(sys.argv) != 2:
        print(f"Использование: python3 {sys.argv[0]} BANK_FILE < requests.txt", file=sys.stderr)
        sys.exit(1)
    banker = load(sys.argv[1])
    safe, sequence = banker.safety()
    print("SAFE, " + " ".join(sequence) if safe else "UNSAFE")

    for raw in sys.stdin:
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split()
        pid = parts[0]
        vector = [int(value) for value in parts[1:]]
        granted = banker.request(pid, vector)
        print(f"request {pid} [{','.join(map(str, vector))}]: {'GRANT' if granted else 'DENY'}")


if __name__ == "__main__":
    main()
