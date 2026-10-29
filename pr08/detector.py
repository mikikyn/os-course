#!/usr/bin/env python3
"""Детектор цикла ожидания для ресурсов с одним экземпляром."""

import sys
from pathlib import Path


def find_cycle(graph: dict[str, set[str]]) -> list[str] | None:
    visited = set()
    stack = []

    def visit(node: str):
        visited.add(node)
        stack.append(node)
        for neighbour in sorted(graph.get(node, set())):
            if neighbour not in visited:
                cycle = visit(neighbour)
                if cycle:
                    return cycle
            elif neighbour in stack:
                return stack[stack.index(neighbour):] + [neighbour]
        stack.pop()
        return None

    for node in sorted(graph):
        if node not in visited:
            cycle = visit(node)
            if cycle:
                return cycle
    return None


def build_graph(path: str | Path) -> dict[str, set[str]]:
    owners = {}
    waits = {}
    for raw in Path(path).read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        action, pid, resource = line.split()
        if action == "acquire":
            owners[resource] = pid
            waits.pop(resource, None)
        elif action == "release":
            if owners.get(resource) == pid:
                owners.pop(resource)
            waits.pop(resource, None)
        elif action == "wait":
            if resource in owners and owners[resource] != pid:
                waits.setdefault(resource, set()).add(pid)
        else:
            raise ValueError(f"Неизвестное событие: {line}")

    graph: dict[str, set[str]] = {}
    for resource, pids in waits.items():
        if resource in owners:
            for pid in pids:
                graph.setdefault(pid, set()).add(owners[resource])
    return graph


def main() -> None:
    if len(sys.argv) != 2:
        print(f"Использование: python3 {sys.argv[0]} LOG", file=sys.stderr)
        sys.exit(1)
    graph = build_graph(sys.argv[1])
    cycle = find_cycle(graph)
    print("DEADLOCK: " + " -> ".join(cycle) if cycle else "NO DEADLOCK")


if __name__ == "__main__":
    main()
