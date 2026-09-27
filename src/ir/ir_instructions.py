"""
Инструкции промежуточного представления (IR).

Каждая инструкция — простой класс с полями.
Есть метод to_str() для печати в читаемом виде.

Используем three-address code:
    t1 = a + b
    x = t1
    if !t1 goto L1
    goto L2
L1:
    return 0
L2:
"""


class IRInstr:
    """Базовый класс для всех инструкций."""
    pass


# ============================================================
# ПРИСВАИВАНИЕ
# ============================================================

class IRAssign(IRInstr):
    """
    Присваивание: dest = src.
    src может быть числом, строкой, идентификатором или bool.
    """

    def __init__(self, dest, src):
        self.dest = dest
        self.src = src

    def to_str(self):
        return f"{self.dest} = {self.src}"


# ============================================================
# БИНАРНЫЕ И УНАРНЫЕ ОПЕРАЦИИ
# ============================================================

class IRBinOp(IRInstr):
    """Бинарная операция: dest = left op right."""

    def __init__(self, dest, op, left, right):
        self.dest = dest
        self.op = op
        self.left = left
        self.right = right

    def to_str(self):
        return f"{self.dest} = {self.left} {self.op} {self.right}"


class IRUnaryOp(IRInstr):
    """Унарная операция: dest = op operand."""

    def __init__(self, dest, op, operand):
        self.dest = dest
        self.op = op
        self.operand = operand

    def to_str(self):
        return f"{self.dest} = {self.op}{self.operand}"


# ============================================================
# ПЕРЕХОДЫ
# ============================================================

class IRLabel(IRInstr):
    """Метка: L1:"""

    def __init__(self, name):
        self.name = name

    def to_str(self):
        return f"{self.name}:"


class IRJump(IRInstr):
    """Безусловный переход: goto L1"""

    def __init__(self, label):
        self.label = label

    def to_str(self):
        return f"goto {self.label}"


class IRJumpIfFalse(IRInstr):
    """Условный переход: if !cond goto L1"""

    def __init__(self, cond, label):
        self.cond = cond
        self.label = label

    def to_str(self):
        return f"if !{self.cond} goto {self.label}"


# ============================================================
# ФУНКЦИИ
# ============================================================

class IRFuncBegin(IRInstr):
    """Начало функции: func name:"""

    def __init__(self, name):
        self.name = name

    def to_str(self):
        return f"func {self.name}:"


class IRCall(IRInstr):
    """Вызов функции: dest = call name(args) или call name(args)."""

    def __init__(self, dest, name, args):
        self.dest = dest      # может быть None
        self.name = name
        self.args = args      # список имён/значений

    def to_str(self):
        args_str = ", ".join(str(a) for a in self.args)
        if self.dest is not None:
            return f"{self.dest} = call {self.name}({args_str})"
        return f"call {self.name}({args_str})"


class IRReturn(IRInstr):
    """Возврат: return value или return."""

    def __init__(self, value):
        self.value = value    # может быть None

    def to_str(self):
        if self.value is None:
            return "return"
        return f"return {self.value}"


# ============================================================
# ПАРАМЕТРЫ (для удобства)
# ============================================================

class IRParam(IRInstr):
    """Параметр функции: param name"""

    def __init__(self, name):
        self.name = name

    def to_str(self):
        return f"param {self.name}"