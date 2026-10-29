#!/usr/bin/env python3
"""Показывает голодание LP и влияние aging на время первого отклика."""

from sched import gantt, metrics, read_processes, simulate


def main() -> None:
    processes = read_processes("starve.txt")
    plain = simulate(processes, "priority")
    aged = simulate(processes, "priority", aging=2)
    plain_metrics = metrics(processes, plain)
    aged_metrics = metrics(processes, aged)

    plain_response = plain_metrics["per_process"]["LP"]["response"]
    aged_response = aged_metrics["per_process"]["LP"]["response"]
    print("Без старения:")
    print(gantt(plain))
    print(f"LP response={plain_response}, среднее ожидание={plain_metrics['average_waiting']:.2f}")
    print("\nСо старением каждые 2 тика:")
    print(gantt(aged))
    print(f"LP response={aged_response}, среднее ожидание={aged_metrics['average_waiting']:.2f}")
    print(f"Улучшение отклика LP: {plain_response - aged_response} тиков")
    if aged_response >= plain_response:
        raise AssertionError("Aging не улучшил время отклика LP")


if __name__ == "__main__":
    main()
