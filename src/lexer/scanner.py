"""
Сканер (лексер). Читает исходник и выдаёт токены по одному.
Работает так: храним позицию, смотрим на текущий символ,
решаем, что это за токен, и сдвигаем позицию.
"""

from .tok import Token, TokKind, KEYWORDS
from .errors import ScanError


class Scanner:
    def __init__(self, source):
        # исходный код
        self.source = source
        # текущая позиция в тексте
        self.pos = 0
        # текущая строка и столбец (начинаем с 1)
        self.line = 1
        self.col = 1
        # для peek_token: запоминаем следующий токен
        self._peeked = None

    # ---------- вспомогательные методы ----------

    def is_at_end(self):
        """Дошли до конца файла?"""
        return self.pos >= len(self.source)

    def _cur(self):
        """Текущий символ или None, если конец."""
        if self.is_at_end():
            return None
        return self.source[self.pos]

    def _peek(self, offset=1):
        """Символ через offset позиций, не сдвигая pos."""
        idx = self.pos + offset
        if idx >= len(self.source):
            return None
        return self.source[idx]

    def _advance(self):
        """Сдвинуть позицию на 1 символ вперёд, обновить line/col."""
        ch = self.source[self.pos]
        self.pos += 1
        if ch == "\n":
            # новая строка
            self.line += 1
            self.col = 1
        else:
            self.col += 1
        return ch

    # ---------- пропуск пробелов и комментариев ----------

    def _skip_whitespace_and_comments(self):
        """
        Пропускаем пробелы, табы, переводы строк и комментарии.
        Вызывается перед каждым токеном.
        """
        while not self.is_at_end():
            ch = self._cur()

            # пробельные символы
            if ch in " \t\r\n":
                self._advance()
                continue

            # однострочный комментарий //
            if ch == "/" and self._peek() == "/":
                # съедаем до конца строки
                while not self.is_at_end() and self._cur() != "\n":
                    self._advance()
                continue

            # многострочный комментарий /* ... */
            if ch == "/" and self._peek() == "*":
                start_line = self.line
                start_col = self.col
                self._advance()  # /
                self._advance()  # *
                closed = False
                while not self.is_at_end():
                    if self._cur() == "*" and self._peek() == "/":
                        self._advance()  # *
                        self._advance()  # /
                        closed = True
                        break
                    self._advance()
                if not closed:
                    raise ScanError("unterminated comment", start_line, start_col)
                continue

            # если не пробел и не комментарий — выходим
            break

    # ---------- главный метод ----------

    def next_token(self):
        """Вернуть следующий токен и сдвинуть позицию."""
        # если уже был peek — отдаём его
        if self._peeked is not None:
            tok = self._peeked
            self._peeked = None
            return tok

        self._skip_whitespace_and_comments()

        if self.is_at_end():
            return Token(TokKind.EOF, "", self.line, self.col)

        start_line = self.line
        start_col = self.col
        ch = self._cur()

        # --- идентификаторы и ключевые слова ---
        if ch.isalpha() or ch == "_":
            return self._read_identifier(start_line, start_col)

        # --- числа ---
        if ch.isdigit():
            return self._read_number(start_line, start_col)

        # --- строки ---
        if ch == '"':
            return self._read_string(start_line, start_col)

        # --- операторы и разделители ---
        return self._read_operator(start_line, start_col)

    def peek_token(self):
        """Посмотреть следующий токен, не сдвигая позицию."""
        if self._peeked is None:
            self._peeked = self.next_token()
        return self._peeked

    def get_line(self):
        return self.line

    def get_column(self):
        return self.col

    # ---------- чтение конкретных токенов ----------

    def _read_identifier(self, line, col):
        """Читаем идентификатор или ключевое слово."""
        start = self.pos
        while not self.is_at_end():
            ch = self._cur()
            if ch.isalnum() or ch == "_":
                self._advance()
            else:
                break
        text = self.source[start:self.pos]

        # проверяем, не ключевое ли это слово
        if text in KEYWORDS:
            return Token(KEYWORDS[text], text, line, col)

        # проверка длины идентификатора (по ТЗ максимум 255)
        if len(text) > 255:
            raise ScanError("identifier too long (max 255)", line, col)

        return Token(TokKind.IDENT, text, line, col)

    def _read_number(self, line, col):
        """Читаем число: целое или вещественное."""
        start = self.pos
        is_float = False

        # целая часть
        while not self.is_at_end() and self._cur().isdigit():
            self._advance()

        # дробная часть
        if not self.is_at_end() and self._cur() == ".":
            # важно: если после точки не цифра — это не float
            if self._peek() is not None and self._peek().isdigit():
                is_float = True
                self._advance()  # точка
                while not self.is_at_end() and self._cur().isdigit():
                    self._advance()

        text = self.source[start:self.pos]

        if is_float:
            value = float(text)
            return Token(TokKind.FLOAT_LIT, text, line, col, value)
        else:
            value = int(text)
            # проверка диапазона int32
            if value < -2**31 or value > 2**31 - 1:
                raise ScanError("integer literal out of range", line, col)
            return Token(TokKind.INT_LIT, text, line, col, value)

    def _read_string(self, line, col):
        """Читаем строковый литерал в двойных кавычках."""
        self._advance()  # открывающая кавычка
        chars = []
        while not self.is_at_end() and self._cur() != '"':
            # обработка переводов строк внутри строки — по ТЗ не разрешено
            if self._cur() == "\n":
                raise ScanError("unterminated string", line, col)
            # простенькая обработка escape-последовательностей
            if self._cur() == "\\":
                self._advance()
                if self.is_at_end():
                    raise ScanError("unterminated string", line, col)
                esc = self._advance()
                if esc == "n":
                    chars.append("\n")
                elif esc == "t":
                    chars.append("\t")
                elif esc == "\\":
                    chars.append("\\")
                elif esc == '"':
                    chars.append('"')
                else:
                    # неизвестный escape — оставляем как есть
                    chars.append(esc)
            else:
                chars.append(self._advance())

        if self.is_at_end():
            raise ScanError("unterminated string", line, col)

        self._advance()  # закрывающая кавычка
        text = '"' + "".join(chars) + '"'
        return Token(TokKind.STRING_LIT, text, line, col, "".join(chars))

    def _read_operator(self, line, col):
        """
        Читаем оператор или разделитель.
        Тут много if-ов, потому что операторы бывают длиной 1 и 2.
        """
        ch = self._advance()
        nxt = self._cur()  # символ после текущего (pos уже сдвинут)

        # --- двухсимвольные операторы ---

        if ch == "=" and nxt == "=":
            self._advance()
            return Token(TokKind.EQ_EQ, "==", line, col)
        if ch == "!" and nxt == "=":
            self._advance()
            return Token(TokKind.NOT_EQ, "!=", line, col)
        if ch == "<" and nxt == "=":
            self._advance()
            return Token(TokKind.LT_EQ, "<=", line, col)
        if ch == ">" and nxt == "=":
            self._advance()
            return Token(TokKind.GT_EQ, ">=", line, col)
        if ch == "&" and nxt == "&":
            self._advance()
            return Token(TokKind.AND_AND, "&&", line, col)
        if ch == "|" and nxt == "|":
            self._advance()
            return Token(TokKind.OR_OR, "||", line, col)
        if ch == "+" and nxt == "=":
            self._advance()
            return Token(TokKind.PLUS_EQ, "+=", line, col)
        if ch == "-" and nxt == "=":
            self._advance()
            return Token(TokKind.MINUS_EQ, "-=", line, col)
        if ch == "*" and nxt == "=":
            self._advance()
            return Token(TokKind.STAR_EQ, "*=", line, col)
        if ch == "/" and nxt == "=":
            self._advance()
            return Token(TokKind.SLASH_EQ, "/=", line, col)
        if ch == "-" and nxt == ">":
            self._advance()
            return Token(TokKind.ARROW, "->", line, col)

        # --- односимвольные операторы ---

        single = {
            "+": TokKind.PLUS,
            "-": TokKind.MINUS,
            "*": TokKind.STAR,
            "/": TokKind.SLASH,
            "%": TokKind.PERCENT,
            "<": TokKind.LT,
            ">": TokKind.GT,
            "!": TokKind.BANG,
            "=": TokKind.ASSIGN,
            "(": TokKind.LPAREN,
            ")": TokKind.RPAREN,
            "{": TokKind.LBRACE,
            "}": TokKind.RBRACE,
            "[": TokKind.LBRACKET,
            "]": TokKind.RBRACKET,
            ";": TokKind.SEMI,
            ",": TokKind.COMMA,
            ":": TokKind.COLON,
        }

        if ch in single:
            return Token(single[ch], ch, line, col)

        # если ничего не подошло — неизвестный символ
        raise ScanError(f"unexpected character {ch!r}", line, col)