"""
CFG — Control Flow Graph.

Граф, где узлы — базовые блоки, а рёбра — переходы между ними.
Хранит все блоки программы и умеет их печатать.
"""

from .basic_block import BasicBlock


class CFG:
    def __init__(self):
        # словарь: имя блока -> BasicBlock
        # порядок добавления сохраняется (Python 3.7+)
        self.blocks = {}
        # имя блока, с которого начинается выполнение
        self.entry = None

    def add_block(self, block):
        """Добавить блок в граф."""
        if block.name in self.blocks:
            raise ValueError(f"duplicate block name: {block.name}")
        self.blocks[block.name] = block

    def get_block(self, name):
        """Получить блок по имени."""
        return self.blocks.get(name)

    def set_entry(self, name):
        """Установить точку входа."""
        self.entry = name

    def connect(self, from_name, to_name):
        """Соединить два блока ребром."""
        frm = self.blocks.get(from_name)
        to = self.blocks.get(to_name)
        if frm is None:
            raise ValueError(f"unknown block: {from_name}")
        if to is None:
            raise ValueError(f"unknown block: {to_name}")
        frm.add_successor(to_name)
        to.add_predecessor(from_name)

    def to_lines(self):
        """
        Напечатать весь CFG.
        Каждый блок — свой раздел.
        """
        lines = []
        for name, block in self.blocks.items():
            lines.extend(block.to_lines())
            # если у блока есть successors, покажем их
            if block.successors:
                lines.append(f"  ; -> {', '.join(block.successors)}")
            lines.append("")  # пустая строка между блоками
        # убираем последнюю пустую строку
        while lines and lines[-1] == "":
            lines.pop()
        return lines