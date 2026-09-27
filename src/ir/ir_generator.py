"""
Генератор IR из AST.

Идея: обходим AST и создаём инструкции IR.
Выражения возвращают имя переменной, где лежит результат.
Операторы просто добавляют инструкции в общий список.

Временные переменные: t1, t2, ...
Метки: L1, L2, ...
"""

from ..parser import ast_nodes
from .ir_instructions import (
    IRAssign, IRBinOp, IRUnaryOp,
    IRLabel, IRJump, IRJumpIfFalse,
    IRFuncBegin, IRCall, IRReturn, IRParam,
)
from .basic_block import BasicBlock
from .control_flow import CFG


class IRGenerator:
    def __init__(self, program):
        self.program = program
        # все инструкции по порядку
        self.instructions = []
        # счётчики для имён
        self.tmp_counter = 0
        self.label_counter = 0
        # CFG
        self.cfg = CFG()
        # текущий блок, в который добавляем инструкции
        self.current_block = None
        # имя текущей функции (для меток)
        self.current_func = None

    # ----------------------------------------------------------
    # вспомогательные методы
    # ----------------------------------------------------------

    def _new_tmp(self):
        """Создать новое имя временной переменной: t1, t2, ..."""
        self.tmp_counter += 1
        return f"t{self.tmp_counter}"

    def _new_label(self):
        """Создать новое имя метки: L1, L2, ..."""
        self.label_counter += 1
        return f"L{self.label_counter}"

    def _emit(self, instr):
        """Добавить инструкцию в текущий блок и в общий список."""
        self.instructions.append(instr)
        if self.current_block is not None:
            self.current_block.add(instr)

    def _start_block(self, name):
        """Создать новый базовый блок и сделать его текущим."""
        block = BasicBlock(name)
        self.cfg.add_block(block)
        self.current_block = block
        return block

    # ----------------------------------------------------------
    # точка входа
    # ----------------------------------------------------------

    def generate(self):
        """Сгенерировать IR для всей программы. Возвращает CFG."""
        for decl in self.program.declarations:
            if isinstance(decl, ast_nodes.FuncDecl):
                self._gen_func(decl)
        return self.cfg

    # ----------------------------------------------------------
    # функции
    # ----------------------------------------------------------

    def _gen_func(self, func):
        """Сгенерировать IR для функции."""
        self.current_func = func.name

        # создаём entry-блок
        entry_name = f"{func.name}_entry"
        self._start_block(entry_name)
        self.cfg.set_entry(entry_name)

        # начало функции
        self._emit(IRFuncBegin(func.name))

        # параметры
        for p in func.params:
            self._emit(IRParam(p.name))

        # тело
        self._gen_block(func.body)

        # конец функции — return без значения (если не было return)
        # чтобы IR был корректным
        self._emit(IRReturn(None))

    # ----------------------------------------------------------
    # операторы
    # ----------------------------------------------------------

    def _gen_block(self, block):
        """Сгенерировать IR для блока { ... }."""
        for stmt in block.statements:
            self._gen_stmt(stmt)

    def _gen_stmt(self, stmt):
        """Сгенерировать IR для одного оператора."""

        if isinstance(stmt, ast_nodes.Block):
            self._gen_block(stmt)

        elif isinstance(stmt, ast_nodes.VarDecl):
            # если есть значение — вычисляем его
            if stmt.value is not None:
                value = self._gen_expr(stmt.value)
                self._emit(IRAssign(stmt.name, value))
            else:
                # без значения — просто 0 (заглушка)
                self._emit(IRAssign(stmt.name, 0))

        elif isinstance(stmt, ast_nodes.If):
            self._gen_if(stmt)

        elif isinstance(stmt, ast_nodes.While):
            self._gen_while(stmt)

        elif isinstance(stmt, ast_nodes.For):
            self._gen_for(stmt)

        elif isinstance(stmt, ast_nodes.Return):
            if stmt.value is not None:
                value = self._gen_expr(stmt.value)
                self._emit(IRReturn(value))
            else:
                self._emit(IRReturn(None))

        elif isinstance(stmt, ast_nodes.ExprStmt):
            self._gen_expr(stmt.expr)

        else:
            raise ValueError(f"unknown statement: {type(stmt).__name__}")

    def _gen_if(self, stmt):
        """
        if (cond) { then } else { else }

        IR:
            t1 = cond
            if !t1 goto L_else
            <then>
            goto L_end
        L_else:
            <else>
        L_end:
        """
        cond = self._gen_expr(stmt.cond)
        else_label = self._new_label()
        end_label = self._new_label()

        # если условие ложно — прыгаем на else
        self._emit(IRJumpIfFalse(cond, else_label))

        # then-ветка
        then_block_name = f"{self.current_func}_{else_label}_then"
        then_block = self._start_block(then_block_name)
        self.cfg.connect(self.cfg.blocks[list(self.cfg.blocks)[-2]].name, then_block_name)
        self._gen_stmt(stmt.then_block)
        self._emit(IRJump(end_label))

        # else-ветка
        else_block_name = f"{self.current_func}_{else_label}_else"
        else_block = self._start_block(else_block_name)
        self.cfg.connect(then_block_name, else_block_name)  # заглушка, потом поправим
        if stmt.else_block is not None:
            self._gen_stmt(stmt.else_block)

        # конец if
        end_block_name = f"{self.current_func}_{end_label}"
        self._start_block(end_block_name)
        self._emit(IRLabel(end_label))

    def _gen_while(self, stmt):
        """
        while (cond) { body }

        IR:
        L_start:
            t1 = cond
            if !t1 goto L_end
            <body>
            goto L_start
        L_end:
        """
        start_label = self._new_label()
        end_label = self._new_label()

        # метка начала цикла
        start_block_name = f"{self.current_func}_{start_label}"
        self._start_block(start_block_name)
        self._emit(IRLabel(start_label))

        # условие
        cond = self._gen_expr(stmt.cond)
        self._emit(IRJumpIfFalse(cond, end_label))

        # тело
        body_block_name = f"{self.current_func}_{start_label}_body"
        self._start_block(body_block_name)
        self._gen_stmt(stmt.body)

        # обратно в начало
        self._emit(IRJump(start_label))

        # конец цикла
        end_block_name = f"{self.current_func}_{end_label}"
        self._start_block(end_block_name)
        self._emit(IRLabel(end_label))

    def _gen_for(self, stmt):
        """
        for (init; cond; step) { body }

        IR:
            <init>
        L_start:
            t1 = cond
            if !t1 goto L_end
            <body>
        L_step:
            <step>
            goto L_start
        L_end:
        """
        # init
        if stmt.init is not None:
            self._gen_stmt(stmt.init)

        start_label = self._new_label()
        step_label = self._new_label()
        end_label = self._new_label()

        # метка начала
        start_block_name = f"{self.current_func}_{start_label}"
        self._start_block(start_block_name)
        self._emit(IRLabel(start_label))

        # условие
        if stmt.cond is not None:
            cond = self._gen_expr(stmt.cond)
            self._emit(IRJumpIfFalse(cond, end_label))

        # тело
        body_block_name = f"{self.current_func}_{start_label}_body"
        self._start_block(body_block_name)
        self._gen_stmt(stmt.body)

        # step
        step_block_name = f"{self.current_func}_{step_label}"
        self._start_block(step_block_name)
        self._emit(IRLabel(step_label))
        if stmt.step is not None:
            self._gen_expr(stmt.step)
        self._emit(IRJump(start_label))

        # конец
        end_block_name = f"{self.current_func}_{end_label}"
        self._start_block(end_block_name)
        self._emit(IRLabel(end_label))

    # ----------------------------------------------------------
    # выражения — возвращают имя переменной, где лежит результат
    # ----------------------------------------------------------

    def _gen_expr(self, expr):
        """Сгенерировать IR для выражения, вернуть имя результата."""

        if isinstance(expr, ast_nodes.IntLit):
            return str(expr.value)

        if isinstance(expr, ast_nodes.FloatLit):
            return str(expr.value)

        if isinstance(expr, ast_nodes.BoolLit):
            return "1" if expr.value else "0"

        if isinstance(expr, ast_nodes.StringLit):
            # строки пока не поддерживаем в IR — возвращаем как есть
            return repr(expr.value)

        if isinstance(expr, ast_nodes.Ident):
            return expr.name

        if isinstance(expr, ast_nodes.BinOp):
            left = self._gen_expr(expr.left)
            right = self._gen_expr(expr.right)
            tmp = self._new_tmp()
            self._emit(IRBinOp(tmp, expr.op, left, right))
            return tmp

        if isinstance(expr, ast_nodes.UnaryOp):
            operand = self._gen_expr(expr.operand)
            tmp = self._new_tmp()
            self._emit(IRUnaryOp(tmp, expr.op, operand))
            return tmp

        if isinstance(expr, ast_nodes.Assign):
            value = self._gen_expr(expr.value)
            # target — это Ident
            self._emit(IRAssign(expr.target.name, value))
            return expr.target.name

        if isinstance(expr, ast_nodes.Call):
            # вычисляем аргументы
            args = []
            for a in expr.args:
                args.append(self._gen_expr(a))
            # если возвращает значение — сохраняем в tmp
            tmp = self._new_tmp()
            self._emit(IRCall(tmp, expr.callee.name, args))
            return tmp

        raise ValueError(f"unknown expression: {type(expr).__name__}")