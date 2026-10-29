#!/usr/bin/env python3
"""Намеренно зависающая программа: запускать только с timeout."""

import threading

lock_a = threading.Lock()
lock_b = threading.Lock()
barrier = threading.Barrier(2)


def worker(first: threading.Lock, second: threading.Lock, label: str) -> None:
    name = threading.current_thread().name
    first.acquire()
    print(f"{name}: захватил {label}", flush=True)
    barrier.wait()
    second.acquire()
    second.release()
    first.release()


def main() -> None:
    threads = [
        threading.Thread(target=worker, args=(lock_a, lock_b, "A"), name="P1"),
        threading.Thread(target=worker, args=(lock_b, lock_a, "B"), name="P2"),
    ]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()


if __name__ == "__main__":
    main()
