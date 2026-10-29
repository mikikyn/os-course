#!/usr/bin/env python3
"""Генерирует numbers.txt с 10 миллионами целых чисел."""

from pathlib import Path

COUNT = 10_000_000
CHUNK = 100_000


def main() -> None:
    output = Path(__file__).with_name("numbers.txt")
    with output.open("w", encoding="ascii", buffering=1024 * 1024) as file:
        for start in range(0, COUNT, CHUNK):
            stop = min(start + CHUNK, COUNT)
            text = "\n".join(str((index * 37) % 10_001 - 5_000) for index in range(start, stop))
            file.write(text + "\n")
    print(f"Создан файл {output}: {COUNT} чисел, {output.stat().st_size} байт")


if __name__ == "__main__":
    main()
