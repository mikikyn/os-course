#!/usr/bin/env python3
"""Намеренно небезопасный счётчик: критическая секция без Lock."""

import threading
import time

counter = 0


def worker() -> None:
    global counter
    for _ in range(100_000):
        current = counter
        time.sleep(0)  # Явно разрешаем переключение между чтением и записью.
        counter = current + 1


def main() -> None:
    global counter
    counter = 0
    threads = [threading.Thread(target=worker) for _ in range(4)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    print(f"Без Lock: counter={counter}, ожидалось=400000, потеряно={400000 - counter}")


if __name__ == "__main__":
    main()
