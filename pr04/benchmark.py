#!/usr/bin/env python3
"""Сравнивает потоки и процессы на CPU-bound и I/O-bound задачах."""

import argparse
import json
import multiprocessing as mp
import os
import statistics
import threading
import time
import urllib.request
from array import array
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

DATA = array("q")
RANGES: list[tuple[int, int]] = []


def sum_range(bounds: tuple[int, int]) -> int:
    start, stop = bounds
    total = 0
    for index in range(start, stop):
        total += DATA[index]
    return total


def cpu_single() -> int:
    return sum_range((0, len(DATA)))


def cpu_threads(executor: ThreadPoolExecutor) -> int:
    return sum(executor.map(sum_range, RANGES))


def cpu_processes(executor: ProcessPoolExecutor) -> int:
    return sum(executor.map(sum_range, RANGES))


def fetch(url: str) -> bytes:
    with urllib.request.urlopen(url, timeout=10) as response:
        return response.read()


def make_network_functions(urls: list[str]):
    def sequential() -> list[bytes]:
        return [fetch(url) for url in urls]

    def threaded() -> list[bytes]:
        with ThreadPoolExecutor(max_workers=4) as executor:
            return list(executor.map(fetch, urls))

    def processed() -> list[bytes]:
        with ProcessPoolExecutor(max_workers=4, mp_context=mp.get_context("fork")) as executor:
            return list(executor.map(fetch, urls))

    return sequential, threaded, processed


def measure(function, repeats: int):
    times = []
    result = None
    for _ in range(repeats):
        start = time.perf_counter()
        result = function()
        times.append(time.perf_counter() - start)
    return result, times


class DelayedHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        time.sleep(0.12)
        body = (f"Ответ для {self.path}\n".encode("utf-8")) * 512
        self.send_response(200)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format: str, *args) -> None:
        pass


def print_table(title: str, rows: dict[str, list[float]], repeats: int) -> None:
    baseline = statistics.median(next(iter(rows.values())))
    print(f"\n{title}; повторов: {repeats}")
    print(f"{'СПОСОБ':<24}{'МЕДИАНА, с':>16}{'УСКОРЕНИЕ':>14}")
    print("-" * 54)
    for name, times in rows.items():
        median = statistics.median(times)
        print(f"{name:<24}{median:>16.4f}{baseline / median:>14.2f}x")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repeats", type=int, default=3)
    args = parser.parse_args()
    if args.repeats < 1:
        parser.error("--repeats должно быть положительным")

    global DATA, RANGES
    numbers_path = Path(__file__).with_name("numbers.txt")
    print(f"Число доступных ядер (os.cpu_count): {os.cpu_count()}")
    print(f"Загрузка {numbers_path.name} (время загрузки в замеры не входит)...", flush=True)
    with numbers_path.open("r", encoding="ascii") as file:
        DATA = array("q", (int(line) for line in file))
    if len(DATA) != 10_000_000:
        raise ValueError(f"Ожидалось 10000000 чисел, получено {len(DATA)}")

    chunk = len(DATA) // 4
    RANGES = [(index * chunk, len(DATA) if index == 3 else (index + 1) * chunk) for index in range(4)]

    cpu_rows = {}
    expected_sum = sum(DATA)
    thread_start = time.perf_counter()
    with ThreadPoolExecutor(max_workers=4) as thread_pool:
        list(thread_pool.map(sum_range, [(0, 1)] * 4))
        thread_startup = time.perf_counter() - thread_start

        process_start = time.perf_counter()
        with ProcessPoolExecutor(max_workers=4, mp_context=mp.get_context("fork")) as process_pool:
            list(process_pool.map(sum_range, [(0, 1)] * 4))
            process_startup = time.perf_counter() - process_start
            print(f"Создание и прогрев пула: 4 потока={thread_startup:.4f} с, 4 процесса={process_startup:.4f} с")

            functions = [
                ("1 поток", cpu_single),
                ("4 потока", lambda: cpu_threads(thread_pool)),
                ("4 процесса", lambda: cpu_processes(process_pool)),
            ]
            for name, function in functions:
                result, times = measure(function, args.repeats)
                if result != expected_sum:
                    raise AssertionError(f"Неверная сумма для {name}: {result} != {expected_sum}")
                cpu_rows[name] = times
    print(f"Контрольная сумма совпала во всех вариантах: {expected_sum}")
    print_table("CPU: сумма 10 000 000 чисел (готовые пулы)", cpu_rows, args.repeats)

    server = ThreadingHTTPServer(("127.0.0.1", 0), DelayedHandler)
    server.daemon_threads = True
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        base = f"http://127.0.0.1:{server.server_port}"
        urls = [f"{base}/file/{index}" for index in range(20)]
        network_rows = {}
        expected_bodies = None
        functions = make_network_functions(urls)
        for name, function in zip(("Последовательно", "4 потока", "4 процесса"), functions):
            bodies, times = measure(function, args.repeats)
            if expected_bodies is None:
                expected_bodies = bodies
            elif bodies != expected_bodies:
                raise AssertionError(f"Разные ответы сервера для {name}")
            network_rows[name] = times
        print_table("I/O: загрузка 20 локальных URL", network_rows, args.repeats)
    finally:
        server.shutdown()
        server.server_close()
        thread.join()

    output = {
        "cpu_count": os.cpu_count(),
        "repeats": args.repeats,
        "numbers": len(DATA),
        "checksum": expected_sum,
        "thread_pool_startup_seconds": thread_startup,
        "process_pool_startup_seconds": process_startup,
        "cpu_seconds": cpu_rows,
        "network_seconds": network_rows,
    }
    output_path = Path(__file__).with_name("benchmark_results.json")
    output_path.write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"\nРезультаты сохранены: {output_path}")


if __name__ == "__main__":
    main()
