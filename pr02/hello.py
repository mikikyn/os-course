#!/usr/bin/env python3
"""Читает файл и выводит его размер в байтах."""

import argparse
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description="Вывести размер файла в байтах")
    parser.add_argument("file", type=Path, help="путь к файлу")
    args = parser.parse_args()

    data = args.file.read_bytes()
    print(f"Файл: {args.file}")
    print(f"Размер: {len(data)} байт")


if __name__ == "__main__":
    main()
