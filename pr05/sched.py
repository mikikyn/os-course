#!/usr/bin/env python3
"""Симулятор FCFS, SJF, SRTF, Priority и Round Robin."""

import argparse
import re
from collections import deque
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Process:
    pid: str
    arrival: int
    burst: int
    priority: int


@dataclass(frozen=True)
class Interval:
    pid: str
    start: int
    end: int


def pid_key(pid: str) -> tuple[int, str]:
    match = re.search(r"\d+", pid)
    return (int(match.group()) if match else 10**9, pid)


def order_key(process: Process) -> tuple[int, tuple[int, str]]:
    return process.arrival, pid_key(process.pid)


def read_processes(path: str | Path) -> list[Process]:
    processes = []
    for number, raw in enumerate(Path(path).read_text(encoding="utf-8").splitlines(), 1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split()
        if len(parts) != 4:
            raise ValueError(f"Строка {number}: нужно PID arrival burst priority")
        pid, arrival, burst, priority = parts
        arrival, burst, priority = int(arrival), int(burst), int(priority)
        if arrival < 0 or burst <= 0:
            raise ValueError(f"Строка {number}: arrival >= 0, burst > 0")
        processes.append(Process(pid, arrival, burst, priority))
    if not processes:
        raise ValueError("Входной файл не содержит процессов")
    return sorted(processes, key=order_key)


def add_interval(intervals: list[Interval], pid: str, start: int, end: int) -> None:
    if start == end:
        return
    if intervals and intervals[-1].pid == pid and intervals[-1].end == start:
        previous = intervals.pop()
        intervals.append(Interval(pid, previous.start, end))
    else:
        intervals.append(Interval(pid, start, end))


def nonpreemptive(processes: list[Process], algorithm: str) -> list[Interval]:
    remaining = set(processes)
    time = min(process.arrival for process in processes)
    intervals: list[Interval] = []
    while remaining:
        available = [process for process in remaining if process.arrival <= time]
        if not available:
            next_arrival = min(process.arrival for process in remaining)
            add_interval(intervals, "IDLE", time, next_arrival)
            time = next_arrival
            continue
        if algorithm == "fcfs":
            chosen = min(available, key=order_key)
        else:
            chosen = min(available, key=lambda process: (process.burst, order_key(process)))
        add_interval(intervals, chosen.pid, time, time + chosen.burst)
        time += chosen.burst
        remaining.remove(chosen)
    return intervals


def preemptive(processes: list[Process], algorithm: str, aging: int | None) -> list[Interval]:
    remaining = {process.pid: process.burst for process in processes}
    executed = {process.pid: 0 for process in processes}
    by_pid = {process.pid: process for process in processes}
    unfinished = set(by_pid)
    time = min(process.arrival for process in processes)
    intervals: list[Interval] = []

    while unfinished:
        available = [by_pid[pid] for pid in unfinished if by_pid[pid].arrival <= time]
        if not available:
            next_arrival = min(by_pid[pid].arrival for pid in unfinished)
            add_interval(intervals, "IDLE", time, next_arrival)
            time = next_arrival
            continue

        if algorithm == "srtf":
            chosen = min(available, key=lambda process: (remaining[process.pid], order_key(process)))
        else:
            def priority_key(process: Process):
                waiting = time - process.arrival - executed[process.pid]
                effective = process.priority
                if aging is not None:
                    effective = max(1, effective - waiting // aging)
                return effective, order_key(process)

            chosen = min(available, key=priority_key)

        add_interval(intervals, chosen.pid, time, time + 1)
        remaining[chosen.pid] -= 1
        executed[chosen.pid] += 1
        time += 1
        if remaining[chosen.pid] == 0:
            unfinished.remove(chosen.pid)
    return intervals


def round_robin(processes: list[Process], quantum: int) -> list[Interval]:
    if quantum <= 0:
        raise ValueError("Квант должен быть положительным")
    pending = deque(processes)
    queue: deque[Process] = deque()
    remaining = {process.pid: process.burst for process in processes}
    time = processes[0].arrival
    intervals: list[Interval] = []

    def arrive_through(current_time: int) -> None:
        while pending and pending[0].arrival <= current_time:
            queue.append(pending.popleft())

    arrive_through(time)
    while queue or pending:
        if not queue:
            next_arrival = pending[0].arrival
            add_interval(intervals, "IDLE", time, next_arrival)
            time = next_arrival
            arrive_through(time)
            continue

        current = queue.popleft()
        duration = min(quantum, remaining[current.pid])
        add_interval(intervals, current.pid, time, time + duration)
        time += duration
        remaining[current.pid] -= duration
        # Сначала прибывшие к моменту t, затем вытесненный в этот же момент.
        arrive_through(time)
        if remaining[current.pid] > 0:
            queue.append(current)
    return intervals


def simulate(processes: list[Process], algorithm: str, **params) -> list[Interval]:
    algorithm = algorithm.lower()
    if algorithm in ("fcfs", "sjf"):
        return nonpreemptive(processes, algorithm)
    if algorithm == "srtf":
        return preemptive(processes, algorithm, None)
    if algorithm == "priority":
        return preemptive(processes, algorithm, params.get("aging"))
    if algorithm == "rr":
        return round_robin(processes, params.get("quantum", 3))
    raise ValueError(f"Неизвестный алгоритм: {algorithm}")


def metrics(processes: list[Process], intervals: list[Interval]) -> dict:
    completion = {process.pid: 0 for process in processes}
    first_start: dict[str, int] = {}
    for interval in intervals:
        if interval.pid == "IDLE":
            continue
        first_start.setdefault(interval.pid, interval.start)
        completion[interval.pid] = interval.end

    per_process = {}
    for process in processes:
        turnaround = completion[process.pid] - process.arrival
        waiting = turnaround - process.burst
        response = first_start[process.pid] - process.arrival
        per_process[process.pid] = {
            "completion": completion[process.pid],
            "turnaround": turnaround,
            "waiting": waiting,
            "response": response,
        }

    count = len(processes)
    makespan = max(interval.end for interval in intervals)
    busy = sum(interval.end - interval.start for interval in intervals if interval.pid != "IDLE")
    switches = sum(
        left.pid != right.pid and left.pid != "IDLE" and right.pid != "IDLE"
        for left, right in zip(intervals, intervals[1:])
    )
    return {
        "per_process": per_process,
        "average_waiting": sum(row["waiting"] for row in per_process.values()) / count,
        "average_turnaround": sum(row["turnaround"] for row in per_process.values()) / count,
        "average_response": sum(row["response"] for row in per_process.values()) / count,
        "cpu_utilization": 100 * busy / makespan if makespan else 100.0,
        "context_switches": switches,
        "makespan": makespan,
    }


def gantt(intervals: list[Interval]) -> str:
    return " ".join(f"[{interval.start:>3}-{interval.end:<3}] {interval.pid}" for interval in intervals)


def print_report(processes: list[Process], intervals: list[Interval]) -> None:
    result = metrics(processes, intervals)
    print("Гант:", gantt(intervals))
    print(f"{'PID':<6}{'END':>6}{'TURN':>7}{'WAIT':>7}{'RESP':>7}")
    for process in processes:
        row = result["per_process"][process.pid]
        print(f"{process.pid:<6}{row['completion']:>6}{row['turnaround']:>7}{row['waiting']:>7}{row['response']:>7}")
    print(f"Среднее ожидание: {result['average_waiting']:.2f}")
    print(f"Средний оборот: {result['average_turnaround']:.2f}")
    print(f"Средний отклик: {result['average_response']:.2f}")
    print(f"Загрузка CPU: {result['cpu_utilization']:.2f}%")
    print(f"Переключений процессов: {result['context_switches']}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("file", help="файл процессов")
    parser.add_argument("--algo", required=True, choices=["fcfs", "sjf", "srtf", "priority", "rr"])
    parser.add_argument("--quantum", type=int, default=3)
    parser.add_argument("--aging", type=int, help="интервал старения для priority")
    args = parser.parse_args()
    if args.aging is not None and args.aging <= 0:
        parser.error("--aging должен быть положительным")

    processes = read_processes(args.file)
    intervals = simulate(processes, args.algo, quantum=args.quantum, aging=args.aging)
    print(f"Файл: {args.file}; алгоритм: {args.algo}; квант: {args.quantum}; aging: {args.aging}")
    print_report(processes, intervals)


if __name__ == "__main__":
    main()
