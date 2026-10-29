#!/usr/bin/env python3
"""Показывает разделение памяти потоками и её копирование процессами."""

import multiprocessing as mp
import threading
from concurrent.futures import ProcessPoolExecutor

items = [0]


def thread_append() -> None:
    items.append(1)


def process_append() -> list[int]:
    items.append(2)
    return items


def main() -> None:
    print(f"До запуска: {items}")
    thread = threading.Thread(target=thread_append)
    thread.start()
    thread.join()
    print(f"После потока в родителе: {items} — изменение видно")

    with ProcessPoolExecutor(max_workers=1, mp_context=mp.get_context("fork")) as executor:
        child_items = executor.submit(process_append).result()
    print(f"Список в дочернем процессе: {child_items}")
    print(f"После процесса в родителе: {items} — изменение ребёнка не видно")


if __name__ == "__main__":
    main()
