"""
Таблица символов и области видимости.

Идея: у нас есть стек областей видимости (scopes).
Когда входим в блок — кладём новый scope.
Когда выходим — снимаем его.

В каждом scope — словарь: имя -> Symbol.
Поиск идентификатора идёт сверху вниз по стеку.
"""


class Symbol:
    """
    Один символ: переменная, функция, структура или параметр.
    """

    def __init__(self, name, kind, var_type=None, params=None, ret_type=None, fields=None):
        self.name = name          # имя
        self.kind = kind          # "var", "func", "struct", "param"
        self.var_type = var_type  # для var/param: тип ("int", "float", ...)
        self.params = params      # для func: список (тип, имя)
        self.ret_type = ret_type  # для func: возвращаемый тип
        self.fields = fields      # для struct: список (тип, имя)

    def __repr__(self):
        return f"Symbol({self.kind} {self.name})"


class SymbolTable:
    """
    Стек областей видимости.

    scopes[0] — глобальный scope (там функции и структуры)
    scopes[-1] — текущий (самый вложенный) scope
    """

    def __init__(self):
        # стек: список словарей {имя: Symbol}
        self.scopes = []
        # сразу создаём глобальный scope
        self.scopes.append({})

    # ----------------------------------------------------------
    # работа со scope
    # ----------------------------------------------------------

    def enter_scope(self):
        """Войти в новую область видимости (блок)."""
        self.scopes.append({})

    def exit_scope(self):
        """Выйти из текущей области видимости."""
        self.scopes.pop()

    def current_scope(self):
        """Текущий (самый вложенный) scope."""
        return self.scopes[-1]

    # ----------------------------------------------------------
    # объявление и поиск
    # ----------------------------------------------------------

    def declare(self, symbol):
        """
        Объявить символ в текущем scope.
        Возвращает False, если имя уже занято в этом scope.
        """
        scope = self.current_scope()
        if symbol.name in scope:
            return False
        scope[symbol.name] = symbol
        return True

    def lookup(self, name):
        """
        Найти символ по имени. Идём от текущего scope к глобальному.
        Возвращает Symbol или None.
        """
        # идём с конца (текущий) к началу (глобальный)
        for scope in reversed(self.scopes):
            if name in scope:
                return scope[name]
        return None

    def lookup_current(self, name):
        """
        Найти символ только в текущем scope.
        Нужно для проверки повторных объявлений.
        """
        return self.current_scope().get(name)