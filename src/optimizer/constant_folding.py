"""
Constant folding и copy propagation.

Constant folding — если оба операнда константы, считаем результат
на этапе компиляции:
    t1 = 2 + 3   ->   t1 = 5

Copy propagation — если переменная равна другой переменной,
подставляем её:
    t1 = x
    y = t1       ->   y = x

Работаем в один проход по списку инструкций.
"""

from ..ir.ir_instructions import (
    IRAssign, IRBinOp, IRUnaryOp,
    IRLabel, IRJump, IRJumpIfFalse,
    IRFuncBegin, IRCall, IRReturn, IRParam,
)


def _is_int(s):
    """Проверить, что строка — целое число."""
    try:
        int(s)
        return True
    except (ValueError, TypeError):
        return False


def _fold_binop(op, left, right):
    """
    Вычислить бинарную операцию над двумя константами.
    Возвращает строку-результат или None, если нельзя.
    """
    if not (_is_int(left) and _is_int(right)):
        return None

    l = int(left)
    r = int(right)

    if op == "+":
        return str(l + r)
    if op == "-":
        return str(l - r)
    if op == "*":
        return str(l * r)
    if op == "/":
        if r == 0:
            return None  # деление на ноль не сворачиваем
        # целочисленное деление как в Python: //, но с учётом знака
        return str(int(l / r))
    if op == "%":
        if r == 0:
            return None
        return str(l % r)
    if op == "==":
        return "1" if l == r else "0"
    if op == "!=":
        return "1" if l != r else "0"
    if op == "<":
        return "1" if l < r else "0"
    if op == "<=":
        return "1" if l <= r else "0"
    if op == ">":
        return "1" if l > r else "0"
    if op == ">=":
        return "1" if l >= r else "0"
    return None


def _fold_unaryop(op, operand):
    """Вычислить унарную операцию над константой."""
    if not _is_int(operand):
        return None
    v = int(operand)
    if op == "-":
        return str(-v)
    if op == "!":
        return "1" if v == 0 else "0"
    return None


def constant_folding(instructions):
    """
    Применить constant folding и copy propagation.
    Возвращает НОВЫЙ список инструкций (не мутируем исходный).
    """
    # сначала соберём информацию о копиях: какая переменная = какая
    # например, t1 = x  ->  copies["t1"] = "x"
    copies = {}

    result = []
    for instr in instructions:
        # сбрасываем копии при входе в новую функцию
        if isinstance(instr, IRFuncBegin):
            copies = {}
            result.append(instr)
            continue

        # сбрасываем копии на метках (чтобы не путать потоки)
        if isinstance(instr, IRLabel):
            copies = {}
            result.append(instr)
            continue

        # --- бинарная операция ---
        if isinstance(instr, IRBinOp):
            left = copies.get(instr.left, instr.left)
            right = copies.get(instr.right, instr.right)
            folded = _fold_binop(instr.op, left, right)
            if folded is not None:
                # заменили на константу
                new = IRAssign(instr.dest, folded)
                result.append(new)
            else:
                new = IRBinOp(instr.dest, instr.op, left, right)
                result.append(new)
                # если left и right — имена, это не копия
            continue

        # --- унарная операция ---
        if isinstance(instr, IRUnaryOp):
            operand = copies.get(instr.operand, instr.operand)
            folded = _fold_unaryop(instr.op, operand)
            if folded is not None:
                new = IRAssign(instr.dest, folded)
                result.append(new)
            else:
                new = IRUnaryOp(instr.dest, instr.op, operand)
                result.append(new)
            continue

        # --- присваивание ---
        if isinstance(instr, IRAssign):
            src = copies.get(instr.src, instr.src)
            new = IRAssign(instr.dest, src)
            result.append(new)
            # если src — имя переменной (не число), запомним копию
            if not _is_int(src) and not _is_float(src):
                copies[instr.dest] = src
            else:
                # dest теперь не копия, а конкретное значение
                copies.pop(instr.dest, None)
            continue

        # --- всё остальное просто копируем ---
        result.append(instr)
        # если это вызов функции — результат может быть неявно изменён
        if isinstance(instr, IRCall):
            # не отслеживаем копии через вызовы (упрощение)
            copies.pop(instr.dest, None) if instr.dest else None

    return result


def _is_float(s):
    """Проверить, что строка — вещественное число."""
    try:
        float(s)
        return "." in str(s)
    except (ValueError, TypeError):
        return False