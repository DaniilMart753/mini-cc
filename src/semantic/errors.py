"""
Ошибки семантического анализа.
Третий вид ошибок после ScanError и ParseError.
"""


class SemanticError(Exception):
    """Ошибка семантического анализа."""

    def __init__(self, message, line, col):
        self.message = message
        self.line = line
        self.col = col
        full = f"[{line}:{col}] semantic error: {message}"
        super().__init__(full)