#!/usr/bin/env python3
"""Небольшой PNG-плоттер на стандартной библиотеке для RR sweep."""

import math
import struct
import zlib
from pathlib import Path

FONT = {
    "0": [14, 17, 19, 21, 25, 17, 14], "1": [4, 12, 4, 4, 4, 4, 14],
    "2": [14, 17, 1, 2, 4, 8, 31], "3": [30, 1, 1, 14, 1, 1, 30],
    "4": [2, 6, 10, 18, 31, 2, 2], "5": [31, 16, 16, 30, 1, 1, 30],
    "6": [14, 16, 16, 30, 17, 17, 14], "7": [31, 1, 2, 4, 8, 8, 8],
    "8": [14, 17, 17, 14, 17, 17, 14], "9": [14, 17, 17, 15, 1, 1, 14],
    "A": [14, 17, 17, 31, 17, 17, 17], "B": [30, 17, 17, 30, 17, 17, 30],
    "C": [14, 17, 16, 16, 16, 17, 14], "D": [30, 17, 17, 17, 17, 17, 30],
    "E": [31, 16, 16, 30, 16, 16, 31], "F": [31, 16, 16, 30, 16, 16, 16],
    "G": [14, 17, 16, 23, 17, 17, 15], "H": [17, 17, 17, 31, 17, 17, 17],
    "I": [14, 4, 4, 4, 4, 4, 14], "J": [7, 2, 2, 2, 18, 18, 12],
    "K": [17, 18, 20, 24, 20, 18, 17], "L": [16, 16, 16, 16, 16, 16, 31],
    "M": [17, 27, 21, 21, 17, 17, 17], "N": [17, 25, 21, 19, 17, 17, 17],
    "O": [14, 17, 17, 17, 17, 17, 14], "P": [30, 17, 17, 30, 16, 16, 16],
    "Q": [14, 17, 17, 17, 21, 18, 13], "R": [30, 17, 17, 30, 20, 18, 17],
    "S": [15, 16, 16, 14, 1, 1, 30], "T": [31, 4, 4, 4, 4, 4, 4],
    "U": [17, 17, 17, 17, 17, 17, 14], "V": [17, 17, 17, 17, 17, 10, 4],
    "W": [17, 17, 17, 21, 21, 21, 10], "X": [17, 17, 10, 4, 10, 17, 17],
    "Y": [17, 17, 10, 4, 4, 4, 4], "Z": [31, 1, 2, 4, 8, 16, 31],
    "-": [0, 0, 0, 31, 0, 0, 0], ".": [0, 0, 0, 0, 0, 12, 12],
    " ": [0, 0, 0, 0, 0, 0, 0],
}


class Canvas:
    def __init__(self, width: int, height: int):
        self.width, self.height = width, height
        self.pixels = bytearray(b"\xff" * (width * height * 3))

    def pixel(self, x: int, y: int, color: tuple[int, int, int]) -> None:
        if 0 <= x < self.width and 0 <= y < self.height:
            offset = (y * self.width + x) * 3
            self.pixels[offset:offset + 3] = bytes(color)

    def line(self, x0: int, y0: int, x1: int, y1: int, color, width: int = 1) -> None:
        dx, sx = abs(x1 - x0), 1 if x0 < x1 else -1
        dy, sy = -abs(y1 - y0), 1 if y0 < y1 else -1
        error = dx + dy
        while True:
            for ox in range(-(width // 2), width // 2 + 1):
                for oy in range(-(width // 2), width // 2 + 1):
                    self.pixel(x0 + ox, y0 + oy, color)
            if x0 == x1 and y0 == y1:
                break
            doubled = 2 * error
            if doubled >= dy:
                error += dy
                x0 += sx
            if doubled <= dx:
                error += dx
                y0 += sy

    def rectangle(self, x: int, y: int, width: int, height: int, color) -> None:
        for yy in range(y, y + height):
            for xx in range(x, x + width):
                self.pixel(xx, yy, color)

    def text(self, x: int, y: int, text: str, color, scale: int = 2) -> None:
        for character in text.upper():
            glyph = FONT.get(character, FONT[" "])
            for row, bits in enumerate(glyph):
                for column in range(5):
                    if bits & (1 << (4 - column)):
                        self.rectangle(x + column * scale, y + row * scale, scale, scale, color)
            x += 6 * scale

    def save(self, path: str | Path) -> None:
        def chunk(kind: bytes, data: bytes) -> bytes:
            return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)

        raw = b"".join(
            b"\x00" + bytes(self.pixels[y * self.width * 3:(y + 1) * self.width * 3])
            for y in range(self.height)
        )
        header = struct.pack(">IIBBBBB", self.width, self.height, 8, 2, 0, 0, 0)
        png = b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", header) + chunk(b"IDAT", zlib.compress(raw, 9)) + chunk(b"IEND", b"")
        Path(path).write_bytes(png)


def nice_max(value: float, step: int) -> int:
    return max(step, math.ceil(value * 1.1 / step) * step)


def write_rr_plot(path: str | Path, rows: list[dict]) -> None:
    canvas = Canvas(1000, 600)
    black, grid, blue, red = (30, 30, 30), (220, 225, 230), (30, 100, 210), (220, 65, 60)
    left, right, top, bottom = 90, 880, 85, 490
    max_wait = nice_max(max(row["waiting"] for row in rows), 10)
    max_switches = nice_max(max(row["switches"] for row in rows), 50)

    canvas.text(285, 24, "RR SWEEP SET2", black, 3)
    canvas.text(90, 57, "AVG WAIT", blue, 2)
    canvas.text(700, 57, "SWITCHES", red, 2)

    for index in range(6):
        y = bottom - index * (bottom - top) // 5
        canvas.line(left, y, right, y, grid)
        canvas.text(35, y - 6, str(max_wait * index // 5), black, 2)
        canvas.text(895, y - 6, str(max_switches * index // 5), black, 2)
    canvas.line(left, top, left, bottom, black, 2)
    canvas.line(right, top, right, bottom, black, 2)
    canvas.line(left, bottom, right, bottom, black, 2)

    wait_points = []
    switch_points = []
    for row in rows:
        x = left + (row["quantum"] - 1) * (right - left) // 9
        wait_y = bottom - round(row["waiting"] / max_wait * (bottom - top))
        switch_y = bottom - round(row["switches"] / max_switches * (bottom - top))
        wait_points.append((x, wait_y))
        switch_points.append((x, switch_y))
        canvas.line(x, bottom, x, bottom + 7, black, 2)
        canvas.text(x - 5, bottom + 16, str(row["quantum"]), black, 2)
    canvas.text(410, 545, "QUANTUM", black, 2)

    for points, color in ((wait_points, blue), (switch_points, red)):
        for first, second in zip(points, points[1:]):
            canvas.line(*first, *second, color, 3)
        for x, y in points:
            canvas.rectangle(x - 3, y - 3, 7, 7, color)
    canvas.save(path)
