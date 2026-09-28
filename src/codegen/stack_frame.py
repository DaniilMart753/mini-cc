"""
Стековый фрейм функции.

В x86-64 стек растёт вниз. Когда функция вызывается:
    push rbp            ; сохраняем старый rbp
    mov rbp, rsp        ; rbp = текущий стек
    sub rsp, N          ; выделяем N байт под локальные переменные

Локальные переменные живут по адресам [rbp-8], [rbp-16], ...
Чем дальше переменная от rbp, тем больше её смещение.

StackFrame хранит:
    - какие переменные уже размещены и по какому смещению
    - сколько всего байт занято (чтобы сделать sub rsp, N)
"""

from .abi import WORD_SIZE


class StackFrame:
    def __init__(self):
        # словарь: имя переменной -> смещение от rbp (отрицательное)
        # например: {"x": -8, "y": -16}
        self.offsets = {}
        # сколько байт занято (положительное число)
        self.size = 0

    def allocate(self, name):
        """
        Выделить место под переменную.
        Возвращает смещение от rbp (например, -8).
        Если переменная уже есть — возвращает её смещение.
        """
        if name in self.offsets:
            return self.offsets[name]

        # сдвигаем на размер слова вниз
        self.size += WORD_SIZE
        offset = -self.size
        self.offsets[name] = offset
        return offset

    def get_offset(self, name):
        """Получить смещение переменной. None, если её нет."""
        return self.offsets.get(name)

    def has(self, name):
        """Есть ли переменная во фрейме?"""
        return name in self.offsets

    def total_size(self):
        """
        Сколько всего байт нужно выделить.
        Округляем вверх до 16 — требование ABI (стек должен быть выровнен).
        """
        size = self.size
        # выравнивание до 16
        if size % 16 != 0:
            size = (size // 16 + 1) * 16
        return size