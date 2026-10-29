#!/usr/bin/env python3
"""Bounded buffer на двух семафорах и мьютексе, без queue.Queue."""

import threading

CAPACITY = 5
TOTAL = 1000
PRODUCERS = 3
CONSUMERS = 2

buffer = [None] * CAPACITY
head = tail = size = 0
empty = threading.Semaphore(CAPACITY)
full = threading.Semaphore(0)
mutex = threading.Lock()
violations: list[str] = []
consumed: list[list[int]] = [[] for _ in range(CONSUMERS)]


def put(item: int | None) -> None:
    global tail, size
    empty.acquire()
    with mutex:
        if size >= CAPACITY:
            violations.append(f"Переполнение при put({item})")
        buffer[tail] = item
        tail = (tail + 1) % CAPACITY
        size += 1
    full.release()


def get() -> int | None:
    global head, size
    full.acquire()
    with mutex:
        if size <= 0:
            violations.append("Чтение пустого буфера")
        item = buffer[head]
        buffer[head] = None
        head = (head + 1) % CAPACITY
        size -= 1
    empty.release()
    return item


def producer(producer_id: int) -> None:
    for item in range(producer_id, TOTAL, PRODUCERS):
        put(item)


def consumer(consumer_id: int) -> None:
    while True:
        item = get()
        if item is None:
            return
        consumed[consumer_id].append(item)


def main() -> None:
    consumers = [threading.Thread(target=consumer, args=(index,)) for index in range(CONSUMERS)]
    producers = [threading.Thread(target=producer, args=(index,)) for index in range(PRODUCERS)]
    for thread in consumers + producers:
        thread.start()
    for thread in producers:
        thread.join()
    for _ in range(CONSUMERS):
        put(None)
    for thread in consumers:
        thread.join()

    result = [item for part in consumed for item in part]
    if violations:
        raise AssertionError(violations)
    if len(result) != TOTAL or set(result) != set(range(TOTAL)):
        raise AssertionError(f"Потеря или дубликат: получено {len(result)}, уникальных {len(set(result))}")
    if size != 0:
        raise AssertionError(f"Буфер не пуст: size={size}")
    print(f"OK semaphore: {TOTAL} элементов, каждый потреблён ровно один раз; переполнений нет")


if __name__ == "__main__":
    main()
