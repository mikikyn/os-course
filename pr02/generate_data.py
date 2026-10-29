#!/usr/bin/env python3
"""Создаёт 50 небольших учебных log-файлов для практической работы."""

import random
import sys
from datetime import datetime, timedelta
from pathlib import Path


def main() -> None:
    output_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).parent / "data"
    output_dir.mkdir(parents=True, exist_ok=True)

    rng = random.Random(42)
    modules = ["net", "auth", "db", "api", "cache"]
    levels = ["INFO", "INFO", "INFO", "WARN", "ERROR"]
    start = datetime(2026, 2, 14, 10, 0, 0)

    for file_number in range(1, 51):
        lines = []
        for line_number in range(60):
            timestamp = start + timedelta(seconds=file_number * 61 + line_number * 7)
            level = rng.choice(levels)
            module = rng.choice(modules)
            lines.append(
                f"{timestamp:%Y-%m-%d %H:%M:%S} {level} "
                f"module={module} msg=учебное событие {line_number + 1}"
            )
        (output_dir / f"{file_number:02d}.log").write_text(
            "\n".join(lines) + "\n", encoding="utf-8"
        )

    print(f"Создано 50 log-файлов: {output_dir}")


if __name__ == "__main__":
    main()
