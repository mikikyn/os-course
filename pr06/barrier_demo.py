#!/usr/bin/env python3
"""Многоразовый барьер на Condition для четырёх потоков и трёх фаз."""

import threading
import time


class ReusableBarrier:
    def __init__(self, parties: int):
        self.parties = parties
        self.count = 0
        self.generation = 0
        self.condition = threading.Condition()

    def wait(self) -> None:
        with self.condition:
            generation = self.generation
            self.count += 1
            if self.count == self.parties:
                self.count = 0
                self.generation += 1
                self.condition.notify_all()
            else:
                while generation == self.generation:
                    self.condition.wait()


barrier = ReusableBarrier(4)
events: list[tuple[int, int, str]] = []
log_lock = threading.Lock()


def log(phase: int, worker_id: int, event: str) -> None:
    with log_lock:
        events.append((phase, worker_id, event))


def worker(worker_id: int) -> None:
    for phase in range(1, 4):
        log(phase, worker_id, "start")
        time.sleep(0.005 * ((worker_id + phase) % 3))
        log(phase, worker_id, "end")
        barrier.wait()
    print(f"Поток {worker_id}: три фазы завершены")


def main() -> None:
    threads = [threading.Thread(target=worker, args=(index,)) for index in range(4)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    for phase in (1, 2):
        last_end = max(index for index, event in enumerate(events) if event[0] == phase and event[2] == "end")
        next_start = min(index for index, event in enumerate(events) if event[0] == phase + 1 and event[2] == "start")
        if last_end > next_start:
            raise AssertionError(f"Поток начал фазу {phase + 1} до конца фазы {phase}")
    print("OK barrier: 4 потока, 3 фазы; ни один поток не начал новую фазу раньше остальных")


if __name__ == "__main__":
    main()
