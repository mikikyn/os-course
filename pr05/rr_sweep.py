#!/usr/bin/env python3
"""Строит таблицу и PNG для квантов RR от 1 до 10 на set2."""

import csv
from pathlib import Path
from plot_png import write_rr_plot
from sched import metrics, read_processes, simulate


def main() -> None:
    processes = read_processes("set2.txt")
    rows = []
    print(f"{'Q':>3}{'AVG WAIT':>12}{'SWITCHES':>12}")
    for quantum in range(1, 11):
        intervals = simulate(processes, "rr", quantum=quantum)
        result = metrics(processes, intervals)
        row = {
            "quantum": quantum,
            "waiting": result["average_waiting"],
            "switches": result["context_switches"],
        }
        rows.append(row)
        print(f"{quantum:>3}{row['waiting']:>12.2f}{row['switches']:>12}")

    with Path("rr_sweep.csv").open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=["quantum", "waiting", "switches"])
        writer.writeheader()
        writer.writerows(rows)
    write_rr_plot("rr_sweep.png", rows)
    print("Созданы rr_sweep.csv и rr_sweep.png")


if __name__ == "__main__":
    main()
