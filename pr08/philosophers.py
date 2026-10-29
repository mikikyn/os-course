#!/usr/bin/env python3
"""Философы: naive с deadlock, ordered и waiter с N−1 за столом."""

import argparse
import threading
import time

COUNT = 5
MEALS = 20


def run_fixed(mode: str) -> None:
    forks = [threading.Lock() for _ in range(COUNT)]
    waiter = threading.Semaphore(COUNT - 1)
    meals = [0] * COUNT

    def philosopher(index: int) -> None:
        left, right = index, (index + 1) % COUNT
        for _ in range(MEALS):
            time.sleep(0.001)
            if mode == "waiter":
                waiter.acquire()
            first, second = (left, right) if mode == "waiter" else sorted((left, right))
            forks[first].acquire()
            forks[second].acquire()
            time.sleep(0.001)
            meals[index] += 1
            forks[second].release()
            forks[first].release()
            if mode == "waiter":
                waiter.release()

    threads = [threading.Thread(target=philosopher, args=(index,), name=f"P{index}") for index in range(COUNT)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=20)
    if any(thread.is_alive() for thread in threads) or meals != [MEALS] * COUNT:
        raise AssertionError(f"mode={mode}, meals={meals}")
    print(f"OK {mode}: meals={meals}")


def run_naive() -> None:
    forks = [threading.Lock() for _ in range(COUNT)]
    left_taken = threading.Barrier(COUNT)
    meals = [0] * COUNT

    def philosopher(index: int) -> None:
        left, right = index, (index + 1) % COUNT
        forks[left].acquire()
        print(f"P{index}: взял левую вилку {left}", flush=True)
        left_taken.wait()
        forks[right].acquire()
        meals[index] += 1
        forks[right].release()
        forks[left].release()

    threads = [threading.Thread(target=philosopher, args=(index,), name=f"P{index}") for index in range(COUNT)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["naive", "ordered", "waiter"], required=True)
    args = parser.parse_args()
    if args.mode == "naive":
        print("Naive: все берут левые вилки, затем ждут правые — ожидается deadlock", flush=True)
        run_naive()
    else:
        run_fixed(args.mode)


if __name__ == "__main__":
    main()
