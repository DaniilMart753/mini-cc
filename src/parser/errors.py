"""
Ошибки, которые может кинуть парсер.
Аналогично ScanError, только для синтаксического анализа.
"""


class ParseError(Exception):
    """Ошибка синтаксического анализа."""

    def __init__(self, message, line, col):
        self.message = message
        self.line = line
        self.col = col
        full = f"[{line}:{col}] parse error: {message}"
        super().__init__(full)