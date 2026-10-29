#!/usr/bin/env python3
"""Детерминированно показывает, почему вокруг Condition.wait нужен while."""

import threading
import time


def demonstrate(use_while: bool) -> str:
    condition = threading.Condition()
    waiting = threading.Event()
    ready = False
    outcome = []

    def consumer() -> None:
        with condition:
            waiting.set()
            if use_while:
                while not ready:
                    condition.wait(timeout=2)
            else:
                if not ready:
                    condition.wait(timeout=2)
            if not ready:
                outcome.append("ОШИБКА: потребитель продолжил без данных")
            else:
                outcome.append("OK: данные получены")

    thread = threading.Thread(target=consumer)
    thread.start()
    waiting.wait()
    with condition:
        condition.notify()  # Имитация пробуждения без выполнения предиката.
    time.sleep(0.1)
    with condition:
        ready = True
        condition.notify()
    thread.join()
    if thread.is_alive():
        raise AssertionError("Потребитель завис")
    return outcome[0]


def main() -> None:
    print(f"if: {demonstrate(False)}")
    print(f"while: {demonstrate(True)}")


if __name__ == "__main__":
    main()
