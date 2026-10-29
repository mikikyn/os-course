"""Общие пути и безопасный вычислитель арифметических выражений."""

import ast
import operator
from pathlib import Path

IPC_DIR = Path(__file__).with_name(".ipc")
REQUEST_FIFO = IPC_DIR / "request.fifo"
RESPONSE_FIFO = IPC_DIR / "response.fifo"
SOCKET_PATH = IPC_DIR / "calc.sock"

BINARY = {ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul, ast.Div: operator.truediv}
UNARY = {ast.UAdd: operator.pos, ast.USub: operator.neg}


def safe_eval(expression: str) -> int | float:
    def evaluate(node: ast.AST) -> int | float:
        if isinstance(node, ast.Expression):
            return evaluate(node.body)
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            return node.value
        if isinstance(node, ast.BinOp) and type(node.op) in BINARY:
            return BINARY[type(node.op)](evaluate(node.left), evaluate(node.right))
        if isinstance(node, ast.UnaryOp) and type(node.op) in UNARY:
            return UNARY[type(node.op)](evaluate(node.operand))
        raise ValueError("разрешены только числа, скобки и операции + - * /")

    return evaluate(ast.parse(expression, mode="eval"))


def answer(expression: str) -> str:
    try:
        return str(safe_eval(expression))
    except (ValueError, SyntaxError, ZeroDivisionError) as error:
        return f"ERROR: {error}"
