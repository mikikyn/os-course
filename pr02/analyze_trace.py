#!/usr/bin/env python3
"""Считает системные вызовы в полном и файловом трассировочных логах."""

import argparse
import re
from pathlib import Path

SYSCALL = re.compile(r"^\d+\s+([A-Za-z_][A-Za-z0-9_]*)\(")


def count_calls(trace_path: Path) -> int:
    return sum(
        bool(SYSCALL.match(line))
        for line in trace_path.read_text(encoding="utf-8").splitlines()
    )


def file_calls(trace_path: Path, sample_path: Path) -> tuple[int, str]:
    lines = trace_path.read_text(encoding="utf-8").splitlines()
    open_pattern = re.compile(r"\b(open|openat)\(")
    descriptor = None
    operations = []

    for line in lines:
        if descriptor is None:
            if str(sample_path) not in line or not open_pattern.search(line):
                continue
            match = re.search(r"=\s+(\d+)(?:\s|$)", line)
            if match is None:
                continue
            descriptor = match.group(1)
            operations.append("openat" if "openat(" in line else "open")
            continue

        fd_operation = re.compile(rf"^\d+\s+(read|readv|close)\({descriptor}(?:,|\))")
        syscall_match = SYSCALL.match(line)
        if fd_operation.search(line) and syscall_match:
            operation = syscall_match.group(1)
            operations.append(operation)
            if operation == "close":
                break

    if descriptor is None:
        return 0, "дескриптор не найден"
    return len(operations), ", ".join(operations)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--python-trace", type=Path, required=True)
    parser.add_argument("--cat-trace", type=Path, required=True)
    parser.add_argument("--sample", type=Path, required=True)
    args = parser.parse_args()

    python_total = count_calls(args.python_trace)
    cat_total = count_calls(args.cat_trace)
    python_file, operations = file_calls(args.python_trace, args.sample)
    cat_file, _ = file_calls(args.cat_trace, args.sample)

    print(f"Python hello.py — всего системных вызовов: {python_total}")
    print(f"Из них открытие, чтение и закрытие {args.sample.name}: {python_file} ({operations})")
    print(f"cat — всего системных вызовов: {cat_total}")
    print(f"Из них открытие, чтение и закрытие {args.sample.name}: {cat_file}")
    print(f"Разница общего числа вызовов Python и cat: {python_total - cat_total}")
    print("Остальные вызовы Python нужны для запуска интерпретатора, загрузки библиотек и модулей, выделения памяти и настройки среды выполнения.")


if __name__ == "__main__":
    main()
