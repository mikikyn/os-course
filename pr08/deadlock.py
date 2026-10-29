#!/usr/bin/env python3
"""Два потока в разном порядке захватывают TrackedLock без зависания."""

import threading
from tracked_lock import DeadlockDetected, TrackedLock

lock_a = TrackedLock("A")
lock_b = TrackedLock("B")
barrier = threading.Barrier(2)


def worker(first: TrackedLock, second: TrackedLock) -> None:
    name = threading.current_thread().name
    first.acquire()
    try:
        barrier.wait()
        try:
            second.acquire()
            second.release()
            print(f"{name}: работа завершена", flush=True)
        except DeadlockDetected as error:
            print(f"{name}: {error}", flush=True)
    finally:
        first.release()


def main() -> None:
    first = threading.Thread(target=worker, args=(lock_a, lock_b), name="P1")
    second = threading.Thread(target=worker, args=(lock_b, lock_a), name="P2")
    first.start()
    second.start()
    first.join(timeout=5)
    second.join(timeout=5)
    if first.is_alive() or second.is_alive():
        raise AssertionError("TrackedLock не предотвратил зависание")
    print("OK TrackedLock: потоки завершились без deadlock")


if __name__ == "__main__":
    main()
