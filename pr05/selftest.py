#!/usr/bin/env python3
"""Сверяет контрольный набор set1 со всеми эталонами методички."""

import math
from sched import metrics, read_processes, simulate

EXPECTED = {
    "fcfs": (8.75, 15.25),
    "sjf": (7.75, 14.25),
    "srtf": (6.50, 13.00),
    "priority": (10.75, 17.25),
    "rr": (13.50, 20.00),
}


def main() -> None:
    processes = read_processes("set1.txt")
    for algorithm, expected in EXPECTED.items():
        intervals = simulate(processes, algorithm, quantum=3)
        result = metrics(processes, intervals)
        actual = result["average_waiting"], result["average_turnaround"]
        if not all(math.isclose(value, reference) for value, reference in zip(actual, expected)):
            raise AssertionError(f"{algorithm}: получено {actual}, эталон {expected}")
        print(f"OK {algorithm}: ожидание={actual[0]:.2f}, оборот={actual[1]:.2f}")
    print("Все пять алгоритмов совпали с эталоном.")


if __name__ == "__main__":
    main()
