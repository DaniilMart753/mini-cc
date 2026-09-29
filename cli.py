"""
CLI для mini-cc.
Запуск: py cli.py scan --input examples/hello.src
"""

import sys
import argparse

from src.lexer import Scanner, ScanError, TokKind
from src.parser import Parser, ParseError
from src.parser import ast_nodes
from src.semantic import SemanticAnalyzer, SemanticError
from src.ir import IRGenerator
from src.codegen import X86Generator
from src.optimizer import Optimizer


def cmd_scan(args):
    """Команда scan: прогнать лексер и напечатать токены."""
    try:
        with open(args.input, "r", encoding="utf-8") as f:
            source = f.read()
    except FileNotFoundError:
        print(f"error: file not found: {args.input}", file=sys.stderr)
        return 1

    scanner = Scanner(source)
    output_lines = []

    while True:
        try:
            tok = scanner.next_token()
        except ScanError as e:
            output_lines.append(f"ERROR {e.line}:{e.col} {e.message}")
            if scanner.is_at_end():
                break
            scanner._advance()
            continue

        output_lines.append(tok.to_output())
        if tok.kind == TokKind.EOF:
            break

    text = "\n".join(output_lines)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(text + "\n")
    else:
        print(text)

    return 0


def cmd_tree(args):
    """Команда tree: разобрать файл и напечатать AST."""
    try:
        with open(args.input, "r", encoding="utf-8") as f:
            source = f.read()
    except FileNotFoundError:
        print(f"error: file not found: {args.input}", file=sys.stderr)
        return 1

    scanner = Scanner(source)
    parser = Parser(scanner)

    try:
        program = parser.parse()
    except (ScanError, ParseError) as e:
        print(f"ERROR {e.line}:{e.col} {e.message}", file=sys.stderr)
        return 1

    lines = []
    _print_node(program, 0, lines)
    text = "\n".join(lines)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(text + "\n")
    else:
        print(text)

    return 0


def cmd_check(args):
    """Команда check: семантический анализ."""
    try:
        with open(args.input, "r", encoding="utf-8") as f:
            source = f.read()
    except FileNotFoundError:
        print(f"error: file not found: {args.input}", file=sys.stderr)
        return 1

    scanner = Scanner(source)
    parser = Parser(scanner)

    try:
        program = parser.parse()
    except (ScanError, ParseError) as e:
        print(f"ERROR {e.line}:{e.col} {e.message}", file=sys.stderr)
        return 1

    analyzer = SemanticAnalyzer(program)
    try:
        analyzer.analyze()
    except SemanticError as e:
        print(f"ERROR {e.line}:{e.col} {e.message}", file=sys.stderr)
        return 1

    print("OK")
    return 0


def cmd_ir(args):
    """Команда ir: сгенерировать IR и напечатать."""
    try:
        with open(args.input, "r", encoding="utf-8") as f:
            source = f.read()
    except FileNotFoundError:
        print(f"error: file not found: {args.input}", file=sys.stderr)
        return 1

    scanner = Scanner(source)
    parser = Parser(scanner)

    try:
        program = parser.parse()
    except (ScanError, ParseError) as e:
        print(f"ERROR {e.line}:{e.col} {e.message}", file=sys.stderr)
        return 1

    analyzer = SemanticAnalyzer(program)
    try:
        analyzer.analyze()
    except SemanticError as e:
        print(f"ERROR {e.line}:{e.col} {e.message}", file=sys.stderr)
        return 1

    generator = IRGenerator(program)
    generator.generate()

    instructions = generator.instructions

    # если указан --optimize — применяем оптимизации
    if getattr(args, "optimize", False):
        opt = Optimizer(instructions)
        instructions = opt.optimize()

    lines = []
    for instr in instructions:
        lines.append(instr.to_str())
    text = "\n".join(lines)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(text + "\n")
    else:
        print(text)

    return 0


def cmd_codegen(args):
    """Команда codegen: сгенерировать x86-64 asm."""
    try:
        with open(args.input, "r", encoding="utf-8") as f:
            source = f.read()
    except FileNotFoundError:
        print(f"error: file not found: {args.input}", file=sys.stderr)
        return 1

    scanner = Scanner(source)
    parser = Parser(scanner)

    try:
        program = parser.parse()
    except (ScanError, ParseError) as e:
        print(f"ERROR {e.line}:{e.col} {e.message}", file=sys.stderr)
        return 1

    analyzer = SemanticAnalyzer(program)
    try:
        analyzer.analyze()
    except SemanticError as e:
        print(f"ERROR {e.line}:{e.col} {e.message}", file=sys.stderr)
        return 1

    ir_gen = IRGenerator(program)
    ir_gen.generate()

    instructions = ir_gen.instructions

    # если указан --optimize — оптимизируем IR перед кодогенерацией
    if getattr(args, "optimize", False):
        opt = Optimizer(instructions)
        instructions = opt.optimize()

    asm_gen = X86Generator(instructions)
    try:
        asm_text = asm_gen.generate()
    except ValueError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(asm_text + "\n")
    else:
        print(asm_text)

    return 0


def _print_node(node, indent, lines):
    """
    Печатаем узел AST с отступом.
    Рекурсивно обходим детей.
    """
    prefix = "  " * indent
    name = node.__class__.__name__

    if isinstance(node, ast_nodes.Program):
        lines.append(f"{prefix}Program")
        for d in node.declarations:
            _print_node(d, indent + 1, lines)

    elif isinstance(node, ast_nodes.FuncDecl):
        params_str = ", ".join(f"{p.var_type} {p.name}" for p in node.params)
        lines.append(f"{prefix}FuncDecl name={node.name} ({params_str}) -> {node.ret_type}")
        _print_node(node.body, indent + 1, lines)

    elif isinstance(node, ast_nodes.StructDecl):
        lines.append(f"{prefix}StructDecl name={node.name}")
        for f in node.fields:
            lines.append(f"{prefix}  Field {f.var_type} {f.name}")

    elif isinstance(node, ast_nodes.Block):
        lines.append(f"{prefix}Block")
        for s in node.statements:
            _print_node(s, indent + 1, lines)

    elif isinstance(node, ast_nodes.VarDecl):
        lines.append(f"{prefix}VarDecl type={node.var_type} name={node.name}")
        if node.value is not None:
            _print_node(node.value, indent + 1, lines)

    elif isinstance(node, ast_nodes.If):
        lines.append(f"{prefix}If")
        lines.append(f"{prefix}  cond:")
        _print_node(node.cond, indent + 2, lines)
        lines.append(f"{prefix}  then:")
        _print_node(node.then_block, indent + 2, lines)
        if node.else_block is not None:
            lines.append(f"{prefix}  else:")
            _print_node(node.else_block, indent + 2, lines)

    elif isinstance(node, ast_nodes.While):
        lines.append(f"{prefix}While")
        lines.append(f"{prefix}  cond:")
        _print_node(node.cond, indent + 2, lines)
        lines.append(f"{prefix}  body:")
        _print_node(node.body, indent + 2, lines)

    elif isinstance(node, ast_nodes.For):
        lines.append(f"{prefix}For")
        if node.init is not None:
            lines.append(f"{prefix}  init:")
            _print_node(node.init, indent + 2, lines)
        if node.cond is not None:
            lines.append(f"{prefix}  cond:")
            _print_node(node.cond, indent + 2, lines)
        if node.step is not None:
            lines.append(f"{prefix}  step:")
            _print_node(node.step, indent + 2, lines)
        lines.append(f"{prefix}  body:")
        _print_node(node.body, indent + 2, lines)

    elif isinstance(node, ast_nodes.Return):
        lines.append(f"{prefix}Return")
        if node.value is not None:
            _print_node(node.value, indent + 1, lines)

    elif isinstance(node, ast_nodes.ExprStmt):
        lines.append(f"{prefix}ExprStmt")
        _print_node(node.expr, indent + 1, lines)

    elif isinstance(node, ast_nodes.IntLit):
        lines.append(f"{prefix}IntLit {node.value}")

    elif isinstance(node, ast_nodes.FloatLit):
        lines.append(f"{prefix}FloatLit {node.value}")

    elif isinstance(node, ast_nodes.StringLit):
        lines.append(f"{prefix}StringLit {node.value!r}")

    elif isinstance(node, ast_nodes.BoolLit):
        lines.append(f"{prefix}BoolLit {node.value}")

    elif isinstance(node, ast_nodes.Ident):
        lines.append(f"{prefix}Ident {node.name}")

    elif isinstance(node, ast_nodes.BinOp):
        lines.append(f"{prefix}BinOp {node.op}")
        _print_node(node.left, indent + 1, lines)
        _print_node(node.right, indent + 1, lines)

    elif isinstance(node, ast_nodes.UnaryOp):
        lines.append(f"{prefix}UnaryOp {node.op}")
        _print_node(node.operand, indent + 1, lines)

    elif isinstance(node, ast_nodes.Assign):
        lines.append(f"{prefix}Assign {node.op}")
        _print_node(node.target, indent + 1, lines)
        _print_node(node.value, indent + 1, lines)

    elif isinstance(node, ast_nodes.Call):
        lines.append(f"{prefix}Call")
        _print_node(node.callee, indent + 1, lines)
        for a in node.args:
            _print_node(a, indent + 1, lines)

    else:
        lines.append(f"{prefix}{name}")


def main():
    parser = argparse.ArgumentParser(
        prog="mini-cc",
        description="Mini compiler for a C-like language",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # scan
    p_scan = sub.add_parser("scan", help="run lexer")
    p_scan.add_argument("--input", required=True, help="source file")
    p_scan.add_argument("--output", help="output file (default: stdout)")
    p_scan.set_defaults(func=cmd_scan)

    # tree
    p_tree = sub.add_parser("tree", help="parse and print AST")
    p_tree.add_argument("--input", required=True, help="source file")
    p_tree.add_argument("--output", help="output file (default: stdout)")
    p_tree.set_defaults(func=cmd_tree)

    # check
    p_check = sub.add_parser("check", help="run semantic analysis")
    p_check.add_argument("--input", required=True, help="source file")
    p_check.set_defaults(func=cmd_check)

    # ir
    p_ir = sub.add_parser("ir", help="generate intermediate representation")
    p_ir.add_argument("--input", required=True, help="source file")
    p_ir.add_argument("--output", help="output file (default: stdout)")
    p_ir.add_argument("--optimize", action="store_true", help="apply optimizations")
    p_ir.set_defaults(func=cmd_ir)

    # codegen
    p_codegen = sub.add_parser("codegen", help="generate x86-64 assembly")
    p_codegen.add_argument("--input", required=True, help="source file")
    p_codegen.add_argument("--output", help="output file (default: stdout)")
    p_codegen.add_argument("--optimize", action="store_true", help="apply optimizations")
    p_codegen.set_defaults(func=cmd_codegen)

    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())