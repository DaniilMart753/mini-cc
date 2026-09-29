"""
Constant folding, copy propagation и constant propagation.

Constant folding — если оба операнда константы, считаем результат:
    t1 = 2 + 3   ->   t1 = 5

Copy propagation — если переменная равна другой переменной, подставляем:
    t1 = x
    y = t1       ->   y = x

Constant propagation — если переменная равна константе, подставляем:
    t1 = 5
    y = t1       ->   y = 5

Всё в одном проходе.
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


def _is_float(s):
    """Проверить, что строка — вещественное число."""
    try:
        float(s)
        return "." in str(s)
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
    Применить constant folding, copy propagation, constant propagation.
    Возвращает НОВЫЙ список инструкций.
    """
    # copies: имя -> значение (число или имя другой переменной)
    # например: {"t1": "5", "x": "t1"}
    copies = {}

    result = []
    for instr in instructions:
        # новая функция — сбрасываем контекст
        if isinstance(instr, IRFuncBegin):
            copies = {}
            result.append(instr)
            continue

        # метка — сбрасываем контекст (разные пути прихода)
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
                new = IRAssign(instr.dest, folded)
                result.append(new)
                copies[instr.dest] = folded
            else:
                new = IRBinOp(instr.dest, instr.op, left, right)
                result.append(new)
                # результат операции не константа — забываем про dest
                copies.pop(instr.dest, None)
            continue

        # --- унарная операция ---
        if isinstance(instr, IRUnaryOp):
            operand = copies.get(instr.operand, instr.operand)
            folded = _fold_unaryop(instr.op, operand)
            if folded is not None:
                new = IRAssign(instr.dest, folded)
                result.append(new)
                copies[instr.dest] = folded
            else:
                new = IRUnaryOp(instr.dest, instr.op, operand)
                result.append(new)
                copies.pop(instr.dest, None)
            continue

        # --- присваивание ---
        if isinstance(instr, IRAssign):
            src = copies.get(instr.src, instr.src)
            new = IRAssign(instr.dest, src)
            result.append(new)
            # запоминаем, чему равен dest
            copies[instr.dest] = src
            continue

        # --- вызов функции ---
        if isinstance(instr, IRCall):
            # аргументы заменяем на известные значения
            new_args = [copies.get(a, a) for a in instr.args]
            new = IRCall(instr.dest, instr.name, new_args)
            result.append(new)
            # результат вызова неизвестен
            if instr.dest:
                copies.pop(instr.dest, None)
            continue

        # --- return ---
        if isinstance(instr, IRReturn):
            if instr.value is not None:
                value = copies.get(instr.value, instr.value)
                new = IRReturn(value)
            else:
                new = instr
            result.append(new)
            continue

        # --- условный переход ---
        if isinstance(instr, IRJumpIfFalse):
            cond = copies.get(instr.cond, instr.cond)
            new = IRJumpIfFalse(cond, instr.label)
            result.append(new)
            continue

        # --- остальное копируем как есть ---
        result.append(instr)

    return result