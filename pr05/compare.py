#!/usr/bin/env python3
"""Сравнивает все алгоритмы на set1, set2 и set3 по четырём метрикам."""

import csv
from pathlib import Path
from sched import metrics, read_processes, simulate


def main() -> None:
    rows = []
    for dataset in ("set1.txt", "set2.txt", "set3.txt"):
        processes = read_processes(dataset)
        print(f"\n{dataset}")
        print(f"{'ALGO':<10}{'WAIT':>10}{'TURN':>10}{'RESP':>10}{'CPU %':>10}{'SWITCH':>10}")
        for algorithm in ("fcfs", "sjf", "srtf", "priority", "rr"):
            intervals = simulate(processes, algorithm, quantum=3)
            result = metrics(processes, intervals)
            row = {
                "dataset": dataset,
                "algorithm": algorithm,
                "waiting": round(result["average_waiting"], 4),
                "turnaround": round(result["average_turnaround"], 4),
                "response": round(result["average_response"], 4),
                "cpu_percent": round(result["cpu_utilization"], 4),
                "switches": result["context_switches"],
            }
            rows.append(row)
            print(
                f"{algorithm:<10}{row['waiting']:>10.2f}{row['turnaround']:>10.2f}"
                f"{row['response']:>10.2f}{row['cpu_percent']:>10.2f}{row['switches']:>10}"
            )

    with Path("comparison.csv").open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    print("\nСоздан comparison.csv")


if __name__ == "__main__":
    main()
