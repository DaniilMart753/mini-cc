"""
Парсер (recursive descent).

Идея: у каждого правила грамматики — своя функция.
Функции вызывают друг друга. Так получается дерево.

Например, для выражений:
    expr   = or_expr
    or_expr = and_expr { "||" and_expr }
    and_expr = eq_expr { "&&" eq_expr }
    ...
    primary = INT | FLOAT | STRING | IDENT | "(" expr ")"
"""

from ..lexer import Scanner, TokKind, ScanError
from .ast_nodes import (
    Program, FuncDecl, StructDecl, Param,
    VarDecl, ExprStmt, Block, If, While, For, Return,
    IntLit, FloatLit, StringLit, BoolLit, Ident,
    BinOp, UnaryOp, Assign, Call,
)
from .errors import ParseError


# какие токены могут начинать тип (int, float, bool, void, struct)
TYPE_TOKENS = {
    TokKind.KW_INT: "int",
    TokKind.KW_FLOAT: "float",
    TokKind.KW_BOOL: "bool",
    TokKind.KW_VOID: "void",
    TokKind.KW_STRUCT: "struct",
}


class Parser:
    def __init__(self, scanner):
        self.scanner = scanner
        # текущий токен
        self.cur = None
        # список уже прочитанных токенов (для отката и peek)
        # на самом деле мы будем просто хранить один текущий
        # и один запасной. Но проще хранить список.
        self._advance()

    # ----------------------------------------------------------
    # вспомогательные методы для работы с токенами
    # ----------------------------------------------------------

    def _advance(self):
        """Взять следующий токен и положить в self.cur."""
        self.cur = self.scanner.next_token()
        return self.cur

    def _check(self, kind):
        """Проверить, что текущий токен — нужного типа."""
        return self.cur.kind == kind

    def _match(self, *kinds):
        """
        Если текущий токен — один из kinds, съесть его и вернуть True.
        Иначе ничего не делать и вернуть False.
        """
        if self.cur.kind in kinds:
            self._advance()
            return True
        return False

    def _expect(self, kind, what):
        """
        Ожидать токен нужного типа. Если его нет — ошибка.
        what — человеческое название для сообщения.
        """
        if self.cur.kind != kind:
            raise ParseError(
                f"expected {what}, got {self.cur.lexeme!r}",
                self.cur.line,
                self.cur.col,
            )
        tok = self.cur
        self._advance()
        return tok

    def _error(self, message):
        """Бросить ParseError с текущей позицией."""
        raise ParseError(message, self.cur.line, self.cur.col)

    # ----------------------------------------------------------
    # точка входа
    # ----------------------------------------------------------

    def parse(self):
        """Разобрать всю программу. Возвращает Program."""
        decls = []
        while not self._check(TokKind.EOF):
            decls.append(self._parse_top_level())
        return Program(decls)

    def _parse_top_level(self):
        """
        Верхний уровень: либо объявление функции (fn ...),
        либо объявление структуры (struct ...).
        """
        if self._check(TokKind.KW_FN):
            return self._parse_func_decl()
        if self._check(TokKind.KW_STRUCT):
            return self._parse_struct_decl()
        self._error(f"expected 'fn' or 'struct', got {self.cur.lexeme!r}")

    # ----------------------------------------------------------
    # объявления
    # ----------------------------------------------------------

    def _parse_func_decl(self):
        """fn name(params) -> type { body }"""
        start = self._expect(TokKind.KW_FN, "'fn'")
        name = self._expect(TokKind.IDENT, "function name").lexeme

        self._expect(TokKind.LPAREN, "'('")

        params = []
        if not self._check(TokKind.RPAREN):
            params.append(self._parse_param())
            while self._match(TokKind.COMMA):
                params.append(self._parse_param())

        self._expect(TokKind.RPAREN, "')'")

        # возвращаемый тип — опционально
        ret_type = "void"
        if self._match(TokKind.ARROW):
            ret_type = self._parse_type()

        body = self._parse_block()
        return FuncDecl(name, params, ret_type, body, start.line, start.col)

    def _parse_param(self):
        """int x, float y, void — параметр функции."""
        type_tok = self.cur
        type_name = self._parse_type()
        name = self._expect(TokKind.IDENT, "parameter name").lexeme
        return Param(type_name, name, type_tok.line, type_tok.col)

    def _parse_type(self):
        """Прочитать тип. Возвращает строку типа."""
        if self.cur.kind in TYPE_TOKENS:
            type_name = TYPE_TOKENS[self.cur.kind]
            self._advance()
            return type_name
        # если это не ключевое слово типа — возможно, struct name
        if self._check(TokKind.IDENT):
            name = self.cur.lexeme
            self._advance()
            return name
        self._error(f"expected type, got {self.cur.lexeme!r}")

    def _parse_struct_decl(self):
        """struct Name { int x; int y; }"""
        start = self._expect(TokKind.KW_STRUCT, "'struct'")
        name = self._expect(TokKind.IDENT, "struct name").lexeme
        self._expect(TokKind.LBRACE, "'{'")

        fields = []
        while not self._check(TokKind.RBRACE) and not self._check(TokKind.EOF):
            type_name = self._parse_type()
            fname = self._expect(TokKind.IDENT, "field name").lexeme
            self._expect(TokKind.SEMI, "';'")
            fields.append(Param(type_name, fname, start.line, start.col))

        self._expect(TokKind.RBRACE, "'}'")
        return StructDecl(name, fields, start.line, start.col)

    # ----------------------------------------------------------
    # операторы
    # ----------------------------------------------------------

    def _parse_block(self):
        """{ stmt* }"""
        start = self._expect(TokKind.LBRACE, "'{'")
        stmts = []
        while not self._check(TokKind.RBRACE) and not self._check(TokKind.EOF):
            stmts.append(self._parse_stmt())
        self._expect(TokKind.RBRACE, "'}'")
        return Block(stmts, start.line, start.col)

    def _parse_stmt(self):
        """Определить, какой это оператор, и разобрать его."""
        # блок
        if self._check(TokKind.LBRACE):
            return self._parse_block()
        # объявление переменной: начинается с типа
        if self.cur.kind in TYPE_TOKENS:
            return self._parse_var_decl()
        # if / while / for / return
        if self._check(TokKind.KW_IF):
            return self._parse_if()
        if self._check(TokKind.KW_WHILE):
            return self._parse_while()
        if self._check(TokKind.KW_FOR):
            return self._parse_for()
        if self._check(TokKind.KW_RETURN):
            return self._parse_return()
        # иначе — выражение
        return self._parse_expr_stmt()

    def _parse_var_decl(self):
        """int x; int y = 5;"""
        start = self.cur
        type_name = self._parse_type()
        name = self._expect(TokKind.IDENT, "variable name").lexeme

        value = None
        if self._match(TokKind.ASSIGN):
            value = self._parse_expr()

        self._expect(TokKind.SEMI, "';'")
        return VarDecl(type_name, name, value, start.line, start.col)

    def _parse_if(self):
        """if (cond) block [else block|stmt]"""
        start = self._expect(TokKind.KW_IF, "'if'")
        self._expect(TokKind.LPAREN, "'('")
        cond = self._parse_expr()
        self._expect(TokKind.RPAREN, "')'")

        then_block = self._parse_block_or_stmt()

        else_block = None
        if self._match(TokKind.KW_ELSE):
            else_block = self._parse_block_or_stmt()

        return If(cond, then_block, else_block, start.line, start.col)

    def _parse_while(self):
        """while (cond) block"""
        start = self._expect(TokKind.KW_WHILE, "'while'")
        self._expect(TokKind.LPAREN, "'('")
        cond = self._parse_expr()
        self._expect(TokKind.RPAREN, "')'")
        body = self._parse_block_or_stmt()
        return While(cond, body, start.line, start.col)

    def _parse_for(self):
        """for (init; cond; step) block"""
        start = self._expect(TokKind.KW_FOR, "'for'")
        self._expect(TokKind.LPAREN, "'('")

        # init: либо объявление переменной, либо выражение, либо ничего
        init = None
        if not self._check(TokKind.SEMI):
            if self.cur.kind in TYPE_TOKENS:
                init = self._parse_var_decl_no_semi()
            else:
                init = self._parse_expr()
        self._expect(TokKind.SEMI, "';'")

        # cond
        cond = None
        if not self._check(TokKind.SEMI):
            cond = self._parse_expr()
        self._expect(TokKind.SEMI, "';'")

        # step
        step = None
        if not self._check(TokKind.RPAREN):
            step = self._parse_expr()
        self._expect(TokKind.RPAREN, "')'")

        body = self._parse_block_or_stmt()
        return For(init, cond, step, body, start.line, start.col)

    def _parse_var_decl_no_semi(self):
        """То же, что _parse_var_decl, но без ';' в конце (для for)."""
        start = self.cur
        type_name = self._parse_type()
        name = self._expect(TokKind.IDENT, "variable name").lexeme
        value = None
        if self._match(TokKind.ASSIGN):
            value = self._parse_expr()
        return VarDecl(type_name, name, value, start.line, start.col)

    def _parse_return(self):
        """return [expr];"""
        start = self._expect(TokKind.KW_RETURN, "'return'")
        value = None
        if not self._check(TokKind.SEMI):
            value = self._parse_expr()
        self._expect(TokKind.SEMI, "';'")
        return Return(value, start.line, start.col)

    def _parse_expr_stmt(self):
        """Выражение как оператор, с ';' в конце."""
        start = self.cur
        expr = self._parse_expr()
        self._expect(TokKind.SEMI, "';'")
        return ExprStmt(expr, start.line, start.col)

    def _parse_block_or_stmt(self):
        """
        В if/while/for тело может быть либо блоком { }, либо одним оператором.
        """
        if self._check(TokKind.LBRACE):
            return self._parse_block()
        return self._parse_stmt()

    # ----------------------------------------------------------
    # выражения (с приоритетами)
    # ----------------------------------------------------------
    # Порядок: or < and < eq < cmp < add < mul < unary < primary
    # Чем ниже — тем сильнее связывает.

    def _parse_expr(self):
        """expr = assignment"""
        return self._parse_assignment()

    def _parse_assignment(self):
        """
        assignment = IDENT ("="|"+="|...) assignment
                   | or_expr
        Правоассоциативно: x = y = 5 разберётся как x = (y = 5).
        """
        # смотрим вперёд: если это IDENT и следующий — оператор присваивания
        # (у нас всего один токен вперёд, поэтому сначала разберём or_expr,
        #  а потом проверим, не идёт ли за ним '=')
        left = self._parse_or()

        if self.cur.kind in (
            TokKind.ASSIGN,
            TokKind.PLUS_EQ,
            TokKind.MINUS_EQ,
            TokKind.STAR_EQ,
            TokKind.SLASH_EQ,
        ):
            op_tok = self.cur
            self._advance()
            right = self._parse_assignment()
            # проверяем, что слева — идентификатор
            if not isinstance(left, Ident):
                raise ParseError(
                    "left side of assignment must be an identifier",
                    op_tok.line,
                    op_tok.col,
                )
            return Assign(op_tok.lexeme, left, right, op_tok.line, op_tok.col)

        return left

    def _parse_or(self):
        """or_expr = and_expr { "||" and_expr }"""
        left = self._parse_and()
        while self._match(TokKind.OR_OR):
            op_tok = self.cur
            right = self._parse_and()
            left = BinOp("||", left, right, left.line, left.col)
        return left

    def _parse_and(self):
        """and_expr = eq_expr { "&&" eq_expr }"""
        left = self._parse_eq()
        while self._match(TokKind.AND_AND):
            right = self._parse_eq()
            left = BinOp("&&", left, right, left.line, left.col)
        return left

    def _parse_eq(self):
        """eq_expr = cmp_expr { ("=="|"!=") cmp_expr }"""
        left = self._parse_cmp()
        while self.cur.kind in (TokKind.EQ_EQ, TokKind.NOT_EQ):
            op = self.cur.lexeme
            self._advance()
            right = self._parse_cmp()
            left = BinOp(op, left, right, left.line, left.col)
        return left

    def _parse_cmp(self):
        """cmp_expr = add_expr { ("<"|"<="|">"|">=") add_expr }"""
        left = self._parse_add()
        while self.cur.kind in (TokKind.LT, TokKind.LT_EQ, TokKind.GT, TokKind.GT_EQ):
            op = self.cur.lexeme
            self._advance()
            right = self._parse_add()
            left = BinOp(op, left, right, left.line, left.col)
        return left

    def _parse_add(self):
        """add_expr = mul_expr { ("+"|"-") mul_expr }"""
        left = self._parse_mul()
        while self.cur.kind in (TokKind.PLUS, TokKind.MINUS):
            op = self.cur.lexeme
            self._advance()
            right = self._parse_mul()
            left = BinOp(op, left, right, left.line, left.col)
        return left

    def _parse_mul(self):
        """mul_expr = unary { ("*"|"/"|"%") unary }"""
        left = self._parse_unary()
        while self.cur.kind in (TokKind.STAR, TokKind.SLASH, TokKind.PERCENT):
            op = self.cur.lexeme
            self._advance()
            right = self._parse_unary()
            left = BinOp(op, left, right, left.line, left.col)
        return left

    def _parse_unary(self):
        """unary = ("-"|"!") unary | primary"""
        if self.cur.kind in (TokKind.MINUS, TokKind.BANG):
            op_tok = self.cur
            op = op_tok.lexeme
            self._advance()
            operand = self._parse_unary()
            return UnaryOp(op, operand, op_tok.line, op_tok.col)
        return self._parse_primary()

    def _parse_primary(self):
        """primary = INT | FLOAT | STRING | true | false | IDENT | call | "(" expr ")" """
        tok = self.cur

        if tok.kind == TokKind.INT_LIT:
            self._advance()
            return IntLit(tok.value, tok.line, tok.col)

        if tok.kind == TokKind.FLOAT_LIT:
            self._advance()
            return FloatLit(tok.value, tok.line, tok.col)

        if tok.kind == TokKind.STRING_LIT:
            self._advance()
            return StringLit(tok.value, tok.line, tok.col)

        if tok.kind == TokKind.KW_TRUE:
            self._advance()
            return BoolLit(True, tok.line, tok.col)

        if tok.kind == TokKind.KW_FALSE:
            self._advance()
            return BoolLit(False, tok.line, tok.col)

        if tok.kind == TokKind.IDENT:
            self._advance()
            # может быть вызов функции: foo(...)
            if self._check(TokKind.LPAREN):
                return self._parse_call(tok)
            return Ident(tok.lexeme, tok.line, tok.col)

        if tok.kind == TokKind.LPAREN:
            self._advance()
            expr = self._parse_expr()
            self._expect(TokKind.RPAREN, "')'")
            return expr

        self._error(f"unexpected token {tok.lexeme!r} in expression")

    def _parse_call(self, name_tok):
        """foo(arg1, arg2)"""
        self._expect(TokKind.LPAREN, "'('")
        args = []
        if not self._check(TokKind.RPAREN):
            args.append(self._parse_expr())
            while self._match(TokKind.COMMA):
                args.append(self._parse_expr())
        self._expect(TokKind.RPAREN, "')'")
        callee = Ident(name_tok.lexeme, name_tok.line, name_tok.col)
        return Call(callee, args, name_tok.line, name_tok.col)