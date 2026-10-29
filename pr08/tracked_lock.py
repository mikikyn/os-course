#!/usr/bin/env python3
"""Lock с графом ожидания: цикл превращается в исключение, а не зависание."""

import itertools
import threading
from detector import find_cycle


class DeadlockDetected(RuntimeError):
    pass


class TrackedLock:
    _counter = itertools.count()
    _graph_lock = threading.Lock()
    _owners: dict[str, str] = {}
    _waiting: dict[str, set[str]] = {}

    def __init__(self, name: str | None = None):
        self.name = name or f"R{next(self._counter)}"
        self._lock = threading.Lock()

    def acquire(self) -> None:
        me = threading.current_thread().name
        with self._graph_lock:
            owner = self._owners.get(self.name)
            if owner is not None and owner != me:
                self._waiting.setdefault(me, set()).add(owner)
                cycle = find_cycle(self._waiting)
                if cycle:
                    self._waiting[me].discard(owner)
                    if not self._waiting[me]:
                        self._waiting.pop(me, None)
                    raise DeadlockDetected("DEADLOCK предотвращён: " + " -> ".join(cycle))
        self._lock.acquire()
        with self._graph_lock:
            self._owners[self.name] = me
            self._waiting.pop(me, None)

    def release(self) -> None:
        me = threading.current_thread().name
        with self._graph_lock:
            if self._owners.get(self.name) != me:
                raise RuntimeError(f"{me} не владеет {self.name}")
            self._owners.pop(self.name, None)
        self._lock.release()

    def __enter__(self):
        self.acquire()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.release()
