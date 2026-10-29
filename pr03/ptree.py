#!/usr/bin/env python3
"""Строит дерево процессов текущего пользователя только по /proc."""

import os
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class Process:
    pid: int
    ppid: int
    name: str
    state: str
    rss: str
    children: list[int] = field(default_factory=list)


def read_process(status_path: Path, uid: int) -> Process | None:
    values: dict[str, str] = {}
    try:
        for line in status_path.read_text(encoding="utf-8").splitlines():
            if ":" in line:
                key, value = line.split(":", 1)
                values[key] = value.strip()
    except (FileNotFoundError, PermissionError, ProcessLookupError):
        return None

    try:
        process_uid = int(values["Uid"].split()[0])
        pid = int(values["Pid"])
        ppid = int(values["PPid"])
    except (KeyError, ValueError, IndexError):
        return None

    if process_uid != uid:
        return None

    return Process(
        pid=pid,
        ppid=ppid,
        name=values.get("Name", "?"),
        state=values.get("State", "?").split()[0],
        rss=values.get("VmRSS", "0 kB"),
    )


def main() -> None:
    uid = os.getuid()
    processes: dict[int, Process] = {}
    for status_path in Path("/proc").glob("[0-9]*/status"):
        process = read_process(status_path, uid)
        if process is not None:
            processes[process.pid] = process

    roots = []
    for process in processes.values():
        if process.ppid in processes and process.ppid != process.pid:
            processes[process.ppid].children.append(process.pid)
        else:
            roots.append(process.pid)

    def print_tree(pid: int, depth: int, visited: set[int]) -> None:
        if pid in visited:
            return
        process = processes[pid]
        print(
            f"{'  ' * depth}PID={process.pid} PPID={process.ppid} "
            f"STATE={process.state} RSS={process.rss} CMD={process.name}"
        )
        visited.add(pid)
        for child_pid in sorted(process.children):
            print_tree(child_pid, depth + 1, visited)

    for root_pid in sorted(roots):
        print_tree(root_pid, 0, set())


if __name__ == "__main__":
    main()
