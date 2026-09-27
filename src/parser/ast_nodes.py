"""
Узлы AST (Abstract Syntax Tree).

AST — это дерево программы. Каждый узел — это какая-то конструкция:
выражение, оператор, объявление. Узлы наследуются от базового Node.

У меня тут получилось много классов, но каждый маленький.
Так проще потом писать семантический анализ — можно проверять isinstance.
"""


class Node:
    """Базовый узел. Все остальные наследуются от него."""

    def __init__(self, line, col):
        self.line = line
        self.col = col

    def __repr__(self):
        return f"{self.__class__.__name__}()"


# ============================================================
# ВЫРАЖЕНИЯ
# ============================================================

class IntLit(Node):
    """Целочисленный литерал: 42"""

    def __init__(self, value, line, col):
        super().__init__(line, col)
        self.value = value


class FloatLit(Node):
    """Вещественный литерал: 3.14"""

    def __init__(self, value, line, col):
        super().__init__(line, col)
        self.value = value


class StringLit(Node):
    """Строковый литерал: "hello" """

    def __init__(self, value, line, col):
        super().__init__(line, col)
        self.value = value


class BoolLit(Node):
    """Булев литерал: true / false"""

    def __init__(self, value, line, col):
        super().__init__(line, col)
        self.value = value


class Ident(Node):
    """Идентификатор: x, foo, bar_baz"""

    def __init__(self, name, line, col):
        super().__init__(line, col)
        self.name = name


class BinOp(Node):
    """Бинарная операция: a + b, x == y, foo && bar"""

    def __init__(self, op, left, right, line, col):
        super().__init__(line, col)
        self.op = op          # строка, например "+" или "=="
        self.left = left      # Node
        self.right = right    # Node


class UnaryOp(Node):
    """Унарная операция: -x, !flag"""

    def __init__(self, op, operand, line, col):
        super().__init__(line, col)
        self.op = op          # строка, например "-" или "!"
        self.operand = operand  # Node


class Assign(Node):
    """Присваивание: x = 5, x += 1"""

    def __init__(self, op, target, value, line, col):
        super().__init__(line, col)
        self.op = op          # "=", "+=", "-=", "*=", "/="
        self.target = target  # Node (Ident)
        self.value = value    # Node


class Call(Node):
    """Вызов функции: foo(1, 2)"""

    def __init__(self, callee, args, line, col):
        super().__init__(line, col)
        self.callee = callee  # Node (Ident)
        self.args = args      # список Node


# ============================================================
# ОПЕРАТОРЫ (STATEMENTS)
# ============================================================

class VarDecl(Node):
    """Объявление переменной: int x = 5;"""

    def __init__(self, var_type, name, value, line, col):
        super().__init__(line, col)
        self.var_type = var_type  # строка, например "int"
        self.name = name          # строка
        self.value = value        # Node или None


class ExprStmt(Node):
    """Выражение как оператор: foo(); x = 5;"""

    def __init__(self, expr, line, col):
        super().__init__(line, col)
        self.expr = expr  # Node


class Block(Node):
    """Блок кода: { ... }"""

    def __init__(self, statements, line, col):
        super().__init__(line, col)
        self.statements = statements  # список Node


class If(Node):
    """Условный оператор: if (cond) { ... } else { ... }"""

    def __init__(self, cond, then_block, else_block, line, col):
        super().__init__(line, col)
        self.cond = cond              # Node
        self.then_block = then_block  # Node (Block)
        self.else_block = else_block  # Node (Block) или None


class While(Node):
    """Цикл while: while (cond) { ... }"""

    def __init__(self, cond, body, line, col):
        super().__init__(line, col)
        self.cond = cond     # Node
        self.body = body     # Node (Block)


class For(Node):
    """Цикл for: for (init; cond; step) { ... }"""

    def __init__(self, init, cond, step, body, line, col):
        super().__init__(line, col)
        self.init = init     # Node или None
        self.cond = cond     # Node или None
        self.step = step     # Node или None
        self.body = body     # Node (Block)


class Return(Node):
    """Оператор return: return x;"""

    def __init__(self, value, line, col):
        super().__init__(line, col)
        self.value = value   # Node или None


# ============================================================
# ОБЪЯВЛЕНИЯ
# ============================================================

class Param(Node):
    """Параметр функции: int x"""

    def __init__(self, var_type, name, line, col):
        super().__init__(line, col)
        self.var_type = var_type
        self.name = name


class FuncDecl(Node):
    """Объявление функции: fn foo(int x) { ... }"""

    def __init__(self, name, params, ret_type, body, line, col):
        super().__init__(line, col)
        self.name = name         # строка
        self.params = params     # список Param
        self.ret_type = ret_type # строка, например "int" или "void"
        self.body = body         # Node (Block)


class StructDecl(Node):
    """Объявление структуры: struct Point { int x; int y; }"""

    def __init__(self, name, fields, line, col):
        super().__init__(line, col)
        self.name = name       # строка
        self.fields = fields   # список Param (имя + тип)


class Program(Node):
    """Корень AST — вся программа."""

    def __init__(self, declarations, line=1, col=1):
        super().__init__(line, col)
        self.declarations = declarations  # список Node