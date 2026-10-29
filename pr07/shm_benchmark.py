#!/usr/bin/env python3
"""Сравнивает передачу 10^7 чисел через shared_memory и Pipe."""

import multiprocessing as mp
import time
from array import array
from multiprocessing.shared_memory import SharedMemory

COUNT = 10_000_000


def shared_worker(name: str, connection) -> None:
    shm = SharedMemory(name=name)
    try:
        view = memoryview(shm.buf).cast("i")
        result = sum(view)
        view.release()
        connection.send(result)
    finally:
        shm.close()
        connection.close()


def pipe_worker(connection) -> None:
    data = connection.recv()
    connection.send(sum(data))
    connection.close()


def main() -> None:
    context = mp.get_context("spawn")
    data = array("i", ((index * 37) % 10_001 - 5_000 for index in range(COUNT)))
    expected = sum(data)
    nbytes = data.itemsize * len(data)

    shm = SharedMemory(create=True, size=nbytes)
    shared_time = None
    try:
        view = memoryview(shm.buf).cast("B")
        view[:] = data.tobytes()
        view.release()
        parent, child = context.Pipe()
        process = context.Process(target=shared_worker, args=(shm.name, child))
        start = time.perf_counter()
        process.start()
        child.close()
        shared_result = parent.recv()
        process.join(timeout=30)
        shared_time = time.perf_counter() - start
        parent.close()
        if process.exitcode != 0 or shared_result != expected:
            raise AssertionError(f"Shared memory: result={shared_result}, exitcode={process.exitcode}")
    finally:
        shm.close()
        shm.unlink()

    parent, child = context.Pipe()
    process = context.Process(target=pipe_worker, args=(child,))
    start = time.perf_counter()
    process.start()
    parent.send(data)
    pipe_result = parent.recv()
    process.join(timeout=30)
    pipe_time = time.perf_counter() - start
    parent.close()
    child.close()
    if process.exitcode != 0 or pipe_result != expected:
        raise AssertionError(f"Pipe: result={pipe_result}, exitcode={process.exitcode}")

    print(f"Элементов: {COUNT}; объём: {nbytes} байт; контрольная сумма: {expected}")
    print(f"{'МЕХАНИЗМ':<20}{'СИНХРОНИЗАЦИЯ':<28}{'ВРЕМЯ, с':>12}")
    print("-" * 60)
    print(f"{'shared_memory':<20}{'нужна при одновременном R/W':<28}{shared_time:>12.4f}")
    print(f"{'Pipe':<20}{'сообщения синхронизирует ОС':<28}{pipe_time:>12.4f}")
    print(f"Pipe/shared memory по времени: {pipe_time / shared_time:.2f}x")
    print("OK: суммы совпали; сегмент shared memory закрыт и удалён")


if __name__ == "__main__":
    main()
