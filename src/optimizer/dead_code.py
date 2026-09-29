"""
Dead code elimination и unreachable code elimination.

Dead code — инструкции, результат которых нигде не используется:
    t1 = 5
    t2 = 10
    return t2     <- t1 не используется, можно удалить

Unreachable code — код после безусловного перехода или return:
    return x
    y = 5         <- недостижимо, можно удалить
    goto L1       <- тоже недостижимо
"""

from ..ir.ir_instructions import (
    IRAssign, IRBinOp, IRUnaryOp,
    IRLabel, IRJump, IRJumpIfFalse,
    IRFuncBegin, IRCall, IRReturn, IRParam,
)


def remove_unreachable(instructions):
    """
    Удалить код после безусловного перехода или return.
    Работаем по блокам: начало блока — метка или начало функции.
    """
    result = []
    dead = False  # флаг: сейчас "мёртвая зона" после goto/return

    for instr in instructions:
        # метка или начало функции — конец мёртвой зоны
        if isinstance(instr, (IRLabel, IRFuncBegin)):
            dead = False
            result.append(instr)
            continue

        # если мы в мёртвой зоне — пропускаем всё, кроме меток
        if dead:
            continue

        result.append(instr)

        # после goto или return — начинается мёртвая зона
        if isinstance(instr, (IRJump, IRReturn)):
            dead = True

    return result


def remove_dead_assigns(instructions):
    """
    Удалить присваивания, результат которых не используется.
    Проходим с конца, собираем множество используемых имён.
    """
    # соберём все используемые имена (в операндах, не в dest)
    # идём с конца — так проще понять, "жив" ли результат
    used = set()
    result = []

    # сначала просто соберём все использования
    for instr in instructions:
        for name in _get_used_names(instr):
            used.add(name)

    # теперь идём сверху и смотрим: если dest нигде не used — удаляем
    # но: у нас used — глобальное множество. Это упрощение.
    # Правильнее — идти с конца, но для учебного проекта сойдёт.
    for instr in instructions:
        if isinstance(instr, IRAssign):
            # если dest не используется и не является "побочным эффектом"
            if instr.dest not in used:
                # не удаляем, если это переменная из исходника
                # (пользователь мог её объявить, но не использовать)
                if _is_temp(instr.dest):
                    continue  # пропускаем — удаляем
            result.append(instr)
        else:
            result.append(instr)

    return result


def _is_temp(name):
    """Временная переменная — t1, t2, ..."""
    if not name.startswith("t"):
        return False
    return name[1:].isdigit()


def _get_used_names(instr):
    """Вернуть список имён, которые инструкция ИСПОЛЬЗУЕТ."""
    used = []

    if isinstance(instr, IRAssign):
        if not _looks_like_number(instr.src):
            used.append(instr.src)

    elif isinstance(instr, IRBinOp):
        if not _looks_like_number(instr.left):
            used.append(instr.left)
        if not _looks_like_number(instr.right):
            used.append(instr.right)

    elif isinstance(instr, IRUnaryOp):
        if not _looks_like_number(instr.operand):
            used.append(instr.operand)

    elif isinstance(instr, IRJumpIfFalse):
        if not _looks_like_number(instr.cond):
            used.append(instr.cond)

    elif isinstance(instr, IRReturn):
        if instr.value is not None and not _looks_like_number(instr.value):
            used.append(instr.value)

    elif isinstance(instr, IRCall):
        for a in instr.args:
            if not _looks_like_number(a):
                used.append(a)

    return used


def _looks_like_number(s):
    """Проверить, что строка похожа на число."""
    if s is None:
        return False
    try:
        float(s)
        return True
    except (ValueError, TypeError):
        return False