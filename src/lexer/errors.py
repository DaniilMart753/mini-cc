"""
Ошибки, которые может кинуть сканер.
Сделал отдельно, чтобы не мешались в scanner.py.
"""


class ScanError(Exception):
    """Ошибка лексического анализа."""

    def __init__(self, message, line, col):
        self.message = message
        self.line = line
        self.col = col
        # формируем красивое сообщение
        full = f"[{line}:{col}] scan error: {message}"
        super().__init__(full)