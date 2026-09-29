from .constant_folding import constant_folding
from .dead_code import remove_unreachable, remove_dead_assigns
from .optimizer import Optimizer

__all__ = [
    "constant_folding",
    "remove_unreachable",
    "remove_dead_assigns",
    "Optimizer",
]