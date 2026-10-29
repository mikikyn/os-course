#!/usr/bin/env python3
"""Исправленный счётчик: инкремент защищён Lock."""

import threading

counter = 0
lock = threading.Lock()


def worker() -> None:
    global counter
    for _ in range(100_000):
        with lock:
            counter += 1


def main() -> None:
    global counter
    counter = 0
    threads = [threading.Thread(target=worker) for _ in range(4)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    if counter != 400_000:
        raise AssertionError(f"counter={counter}")
    print(f"OK Lock: counter={counter}, ожидалось=400000")


if __name__ == "__main__":
    main()
