"""
Семантический анализатор.

Работает в два прохода:
1. Собираем все объявления (функции, структуры) в глобальный scope.
   Это нужно, чтобы функция могла вызывать функцию, объявленную позже.
2. Обходим тела функций и проверяем:
   - все ли имена объявлены
   - совпадают ли типы
   - правильные ли аргументы у вызовов
   - правильный ли return
"""

from ..parser import ast_nodes
from ..parser import ParseError  # not used, но пусть будет на будущее
from .errors import SemanticError
from .symbol_table import SymbolTable, Symbol


# какие типы у нас есть
BASE_TYPES = {"int", "float", "bool", "void", "string"}


class SemanticAnalyzer:
    def __init__(self, program):
        self.program = program
        self.table = SymbolTable()
        # текущая функция (нужна, чтобы знать, что возвращать)
        self.current_func = None

    # ==========================================================
    # точка входа
    # ==========================================================

    def analyze(self):
        """Проанализировать программу. Возвращает SymbolTable."""
        # первый проход: собираем объявления верхнего уровня
        self._collect_declarations()

        # второй проход: обходим тела функций
        for decl in self.program.declarations:
            if isinstance(decl, ast_nodes.FuncDecl):
                self._check_func(decl)

        return self.table

    # ==========================================================
    # первый проход: сбор объявлений
    # ==========================================================

    def _collect_declarations(self):
        """Собрать функции и структуры в глобальный scope."""
        for decl in self.program.declarations:
            if isinstance(decl, ast_nodes.FuncDecl):
                # проверяем, что возвращаемый тип существует
                if decl.ret_type not in BASE_TYPES and decl.ret_type != "void":
                    # возможно, это структура
                    if self.table.lookup(decl.ret_type) is None:
                        raise SemanticError(
                            f"unknown return type {decl.ret_type!r}",
                            decl.line,
                            decl.col,
                        )

                # параметры
                param_list = []
                seen_names = set()
                for p in decl.params:
                    if p.name in seen_names:
                        raise SemanticError(
                            f"duplicate parameter {p.name!r}",
                            p.line,
                            p.col,
                        )
                    seen_names.add(p.name)
                    if p.var_type not in BASE_TYPES and self.table.lookup(p.var_type) is None:
                        raise SemanticError(
                            f"unknown type {p.var_type!r}",
                            p.line,
                            p.col,
                        )
                    param_list.append((p.var_type, p.name))

                sym = Symbol(
                    decl.name,
                    "func",
                    params=param_list,
                    ret_type=decl.ret_type,
                )
                if not self.table.declare(sym):
                    raise SemanticError(
                        f"redeclaration of function {decl.name!r}",
                        decl.line,
                        decl.col,
                    )

            elif isinstance(decl, ast_nodes.StructDecl):
                fields = []
                seen = set()
                for f in decl.fields:
                    if f.name in seen:
                        raise SemanticError(
                            f"duplicate field {f.name!r} in struct {decl.name!r}",
                            f.line,
                            f.col,
                        )
                    seen.add(f.name)
                    if f.var_type not in BASE_TYPES and self.table.lookup(f.var_type) is None:
                        raise SemanticError(
                            f"unknown type {f.var_type!r}",
                            f.line,
                            f.col,
                        )
                    fields.append((f.var_type, f.name))

                sym = Symbol(decl.name, "struct", fields=fields)
                if not self.table.declare(sym):
                    raise SemanticError(
                        f"redeclaration of struct {decl.name!r}",
                        decl.line,
                        decl.col,
                    )

    # ==========================================================
    # второй проход: проверка функций
    # ==========================================================

    def _check_func(self, func):
        """Проверить тело функции."""
        self.current_func = func

        # входим в новый scope (для параметров и локальных переменных)
        self.table.enter_scope()

        # объявляем параметры
        for p in func.params:
            sym = Symbol(p.name, "param", var_type=p.var_type)
            self.table.declare(sym)

        # проверяем тело
        self._check_stmt(func.body)

        self.table.exit_scope()
        self.current_func = None

    # ==========================================================
    # проверка операторов
    # ==========================================================

    def _check_stmt(self, stmt):
        """Проверить оператор."""

        if isinstance(stmt, ast_nodes.Block):
            # новый scope для блока
            self.table.enter_scope()
            for s in stmt.statements:
                self._check_stmt(s)
            self.table.exit_scope()

        elif isinstance(stmt, ast_nodes.VarDecl):
            # проверяем значение (если есть)
            if stmt.value is not None:
                value_type = self._check_expr(stmt.value)
                if not self._types_compatible(stmt.var_type, value_type):
                    raise SemanticError(
                        f"cannot assign {value_type!r} to variable of type {stmt.var_type!r}",
                        stmt.line,
                        stmt.col,
                    )

            # проверяем, что тип существует
            if stmt.var_type not in BASE_TYPES and self.table.lookup(stmt.var_type) is None:
                raise SemanticError(
                    f"unknown type {stmt.var_type!r}",
                    stmt.line,
                    stmt.col,
                )

            # объявляем переменную
            sym = Symbol(stmt.name, "var", var_type=stmt.var_type)
            if not self.table.declare(sym):
                raise SemanticError(
                    f"redeclaration of variable {stmt.name!r}",
                    stmt.line,
                    stmt.col,
                )

        elif isinstance(stmt, ast_nodes.If):
            cond_type = self._check_expr(stmt.cond)
            if cond_type != "bool":
                raise SemanticError(
                    f"if condition must be bool, got {cond_type!r}",
                    stmt.cond.line,
                    stmt.cond.col,
                )
            self._check_stmt(stmt.then_block)
            if stmt.else_block is not None:
                self._check_stmt(stmt.else_block)

        elif isinstance(stmt, ast_nodes.While):
            cond_type = self._check_expr(stmt.cond)
            if cond_type != "bool":
                raise SemanticError(
                    f"while condition must be bool, got {cond_type!r}",
                    stmt.cond.line,
                    stmt.cond.col,
                )
            self._check_stmt(stmt.body)

        elif isinstance(stmt, ast_nodes.For):
            # init, cond, step могут быть None
            self.table.enter_scope()
            if stmt.init is not None:
                self._check_stmt(stmt.init)
            if stmt.cond is not None:
                cond_type = self._check_expr(stmt.cond)
                if cond_type != "bool":
                    raise SemanticError(
                        f"for condition must be bool, got {cond_type!r}",
                        stmt.cond.line,
                        stmt.cond.col,
                    )
            if stmt.step is not None:
                self._check_expr(stmt.step)
            self._check_stmt(stmt.body)
            self.table.exit_scope()

        elif isinstance(stmt, ast_nodes.Return):
            if stmt.value is not None:
                value_type = self._check_expr(stmt.value)
                if not self._types_compatible(self.current_func.ret_type, value_type):
                    raise SemanticError(
                        f"cannot return {value_type!r} from function returning {self.current_func.ret_type!r}",
                        stmt.line,
                        stmt.col,
                    )
            else:
                # return без значения — только для void
                if self.current_func.ret_type != "void":
                    raise SemanticError(
                        f"function {self.current_func.name!r} must return {self.current_func.ret_type!r}",
                        stmt.line,
                        stmt.col,
                    )

        elif isinstance(stmt, ast_nodes.ExprStmt):
            self._check_expr(stmt.expr)

        else:
            raise SemanticError(
                f"unknown statement type: {type(stmt).__name__}",
                stmt.line,
                stmt.col,
            )

    # ==========================================================
    # проверка выражений — возвращает тип
    # ==========================================================

    def _check_expr(self, expr):
        """Проверить выражение. Возвращает тип ('int', 'float', ...)."""

        if isinstance(expr, ast_nodes.IntLit):
            return "int"

        if isinstance(expr, ast_nodes.FloatLit):
            return "float"

        if isinstance(expr, ast_nodes.StringLit):
            return "string"

        if isinstance(expr, ast_nodes.BoolLit):
            return "bool"

        if isinstance(expr, ast_nodes.Ident):
            sym = self.table.lookup(expr.name)
            if sym is None:
                raise SemanticError(
                    f"undefined name {expr.name!r}",
                    expr.line,
                    expr.col,
                )
            if sym.kind == "func":
                raise SemanticError(
                    f"{expr.name!r} is a function, not a value",
                    expr.line,
                    expr.col,
                )
            return sym.var_type

        if isinstance(expr, ast_nodes.BinOp):
            return self._check_binop(expr)

        if isinstance(expr, ast_nodes.UnaryOp):
            return self._check_unary(expr)

        if isinstance(expr, ast_nodes.Assign):
            return self._check_assign(expr)

        if isinstance(expr, ast_nodes.Call):
            return self._check_call(expr)

        raise SemanticError(
            f"unknown expression type: {type(expr).__name__}",
            expr.line,
            expr.col,
        )

    # ----------------------------------------------------------
    # бинарные операции
    # ----------------------------------------------------------

    def _check_binop(self, expr):
        left = self._check_expr(expr.left)
        right = self._check_expr(expr.right)
        op = expr.op

        # арифметика: + - * / %
        if op in ("+", "-", "*", "/", "%"):
            # частный случай: string + string -> string
            if op == "+" and left == "string" and right == "string":
                return "string"
            # числа
            if left in ("int", "float") and right in ("int", "float"):
                # если хоть один float — результат float
                if left == "float" or right == "float":
                    return "float"
                return "int"
            raise SemanticError(
                f"invalid operands for {op!r}: {left!r} and {right!r}",
                expr.line,
                expr.col,
            )

        # сравнения: == != < <= > >=
        if op in ("==", "!=", "<", "<=", ">", ">="):
            # разрешаем сравнивать числа между собой и string со string
            if left in ("int", "float") and right in ("int", "float"):
                return "bool"
            if left == "string" and right == "string":
                return "bool"
            if left == "bool" and right == "bool":
                return "bool"
            raise SemanticError(
                f"cannot compare {left!r} and {right!r}",
                expr.line,
                expr.col,
            )

        # логика: && ||
        if op in ("&&", "||"):
            if left != "bool" or right != "bool":
                raise SemanticError(
                    f"logical operator {op!r} requires bool operands, got {left!r} and {right!r}",
                    expr.line,
                    expr.col,
                )
            return "bool"

        raise SemanticError(
            f"unknown binary operator {op!r}",
            expr.line,
            expr.col,
        )

    # ----------------------------------------------------------
    # унарные операции
    # ----------------------------------------------------------

    def _check_unary(self, expr):
        operand = self._check_expr(expr.operand)
        op = expr.op

        if op == "-":
            if operand not in ("int", "float"):
                raise SemanticError(
                    f"unary '-' requires number, got {operand!r}",
                    expr.line,
                    expr.col,
                )
            return operand

        if op == "!":
            if operand != "bool":
                raise SemanticError(
                    f"unary '!' requires bool, got {operand!r}",
                    expr.line,
                    expr.col,
                )
            return "bool"

        raise SemanticError(
            f"unknown unary operator {op!r}",
            expr.line,
            expr.col,
        )

    # ----------------------------------------------------------
    # присваивание
    # ----------------------------------------------------------

    def _check_assign(self, expr):
        # target должен быть Ident
        # (парсер это уже гарантирует, но проверим)
        if not isinstance(expr.target, ast_nodes.Ident):
            raise SemanticError(
                "assignment target must be an identifier",
                expr.line,
                expr.col,
            )

        sym = self.table.lookup(expr.target.name)
        if sym is None:
            raise SemanticError(
                f"undefined name {expr.target.name!r}",
                expr.target.line,
                expr.target.col,
            )
        if sym.kind == "func":
            raise SemanticError(
                f"cannot assign to function {expr.target.name!r}",
                expr.line,
                expr.col,
            )

        value_type = self._check_expr(expr.value)

        if not self._types_compatible(sym.var_type, value_type):
            raise SemanticError(
                f"cannot assign {value_type!r} to variable of type {sym.var_type!r}",
                expr.line,
                expr.col,
            )

        return sym.var_type

    # ----------------------------------------------------------
    # вызов функции
    # ----------------------------------------------------------

    def _check_call(self, expr):
        # callee должен быть Ident
        if not isinstance(expr.callee, ast_nodes.Ident):
            raise SemanticError(
                "call target must be an identifier",
                expr.line,
                expr.col,
            )

        sym = self.table.lookup(expr.callee.name)
        if sym is None:
            raise SemanticError(
                f"undefined function {expr.callee.name!r}",
                expr.line,
                expr.col,
            )
        if sym.kind != "func":
            raise SemanticError(
                f"{expr.callee.name!r} is not a function",
                expr.line,
                expr.col,
            )

        # проверяем количество аргументов
        if len(expr.args) != len(sym.params):
            raise SemanticError(
                f"function {expr.callee.name!r} expects {len(sym.params)} arguments, got {len(expr.args)}",
                expr.line,
                expr.col,
            )

        # проверяем типы аргументов
        for i, arg in enumerate(expr.args):
            arg_type = self._check_expr(arg)
            expected = sym.params[i][0]
            if not self._types_compatible(expected, arg_type):
                raise SemanticError(
                    f"argument {i + 1} of {expr.callee.name!r}: expected {expected!r}, got {arg_type!r}",
                    arg.line,
                    arg.col,
                )

        return sym.ret_type

    # ----------------------------------------------------------
    # совместимость типов
    # ----------------------------------------------------------

    def _types_compatible(self, expected, actual):
        """
        Проверить, можно ли присвоить значение типа actual
        переменной типа expected.
        """
        if expected == actual:
            return True
        # int можно присвоить во float
        if expected == "float" and actual == "int":
            return True
        return False