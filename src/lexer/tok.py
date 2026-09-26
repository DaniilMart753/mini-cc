"""
Тут лежат все типы токенов и сам класс Token.
Я решил вынести это в отдельный файл, чтобы scanner.py не разрастался.
"""

from enum import Enum, auto


class TokKind(Enum):
    # ключевые слова
    KW_IF = auto()
    KW_ELSE = auto()
    KW_WHILE = auto()
    KW_FOR = auto()
    KW_INT = auto()
    KW_FLOAT = auto()
    KW_BOOL = auto()
    KW_RETURN = auto()
    KW_TRUE = auto()
    KW_FALSE = auto()
    KW_VOID = auto()
    KW_STRUCT = auto()
    KW_FN = auto()

    # идентификаторы и литералы
    IDENT = auto()
    INT_LIT = auto()
    FLOAT_LIT = auto()
    STRING_LIT = auto()
    BOOL_LIT = auto()

    # арифметика
    PLUS = auto()
    MINUS = auto()
    STAR = auto()
    SLASH = auto()
    PERCENT = auto()

    # сравнения
    EQ_EQ = auto()
    NOT_EQ = auto()
    LT = auto()
    LT_EQ = auto()
    GT = auto()
    GT_EQ = auto()

    # логика
    AND_AND = auto()
    OR_OR = auto()
    BANG = auto()

    # присваивание
    ASSIGN = auto()
    PLUS_EQ = auto()
    MINUS_EQ = auto()
    STAR_EQ = auto()
    SLASH_EQ = auto()

    # разделители
    LPAREN = auto()
    RPAREN = auto()
    LBRACE = auto()
    RBRACE = auto()
    LBRACKET = auto()
    RBRACKET = auto()
    SEMI = auto()
    COMMA = auto()
    COLON = auto()
    ARROW = auto()

    # конец файла
    EOF = auto()


# словарь ключевых слов: строка -> тип токена
# так удобнее, чем писать кучу if-ов
KEYWORDS = {
    "if": TokKind.KW_IF,
    "else": TokKind.KW_ELSE,
    "while": TokKind.KW_WHILE,
    "for": TokKind.KW_FOR,
    "int": TokKind.KW_INT,
    "float": TokKind.KW_FLOAT,
    "bool": TokKind.KW_BOOL,
    "return": TokKind.KW_RETURN,
    "true": TokKind.KW_TRUE,
    "false": TokKind.KW_FALSE,
    "void": TokKind.KW_VOID,
    "struct": TokKind.KW_STRUCT,
    "fn": TokKind.KW_FN,
}


class Token:
    """
    Один токен.
    kind   - тип (из TokKind)
    lexeme - как это выглядит в исходнике (строка)
    line   - номер строки (с 1)
    col    - номер столбца (с 1)
    value  - значение для литералов (int/float/bool/str), иначе None
    """

    def __init__(self, kind, lexeme, line, col, value=None):
        self.kind = kind
        self.lexeme = lexeme
        self.line = line
        self.col = col
        self.value = value

    def __repr__(self):
        # удобно для отладки
        return f"Token({self.kind.name}, {self.lexeme!r}, {self.line}:{self.col})"

    def to_output(self):
        """
        Формат вывода как в ТЗ:
        LINE:COLUMN TOKEN_TYPE "LEXEME" [LITERAL_VALUE]
        """
        base = f'{self.line}:{self.col} {self.kind.name} "{self.lexeme}"'
        if self.value is not None:
            base += f" {self.value}"
        return base