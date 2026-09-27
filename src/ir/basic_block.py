"""
Базовый блок (basic block).

Базовый блок — это последовательность инструкций,
в которую вход только в начале, а выход — только в конце.
Внутри нет переходов.

Пример:
    block1:
        x = 10
        t1 = x > 5
        if !t1 goto L1   <- конец блока
    block2 (L1):
        return 0
"""


class BasicBlock:
    def __init__(self, name):
        self.name = name           # имя блока (например, "main_entry")
        self.instructions = []     # список IRInstr
        # рёбра CFG: имена блоков, куда можно перейти
        self.successors = []       # куда ведут переходы
        self.predecessors = []     # откуда приходят

    def add(self, instr):
        """Добавить инструкцию в конец блока."""
        self.instructions.append(instr)

    def add_successor(self, block_name):
        """Добавить ребро в CFG."""
        if block_name not in self.successors:
            self.successors.append(block_name)

    def add_predecessor(self, block_name):
        """Добавить обратное ребро."""
        if block_name not in self.predecessors:
            self.predecessors.append(block_name)

    def is_empty(self):
        return len(self.instructions) == 0

    def last(self):
        """Последняя инструкция блока (или None)."""
        if not self.instructions:
            return None
        return self.instructions[-1]

    def to_lines(self):
        """Список строк для печати блока."""
        lines = [f"{self.name}:"]
        for instr in self.instructions:
            lines.append(f"  {instr.to_str()}")
        return lines

    def __repr__(self):
        return f"BasicBlock({self.name}, {len(self.instructions)} instrs)"