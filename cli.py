"""
CLI для mini-cc.
Запуск: py cli.py scan --input examples/hello.src
"""

import sys
import argparse

from src.lexer import Scanner, ScanError, TokKind


def cmd_scan(args):
    """Команда scan: прогнать лексер и напечатать токены."""
    # читаем файл
    try:
        with open(args.input, "r", encoding="utf-8") as f:
            source = f.read()
    except FileNotFoundError:
        print(f"error: file not found: {args.input}", file=sys.stderr)
        return 1

    scanner = Scanner(source)
    output_lines = []

    # собираем токены, пока не EOF
    while True:
        try:
            tok = scanner.next_token()
        except ScanError as e:
            # по ТЗ: сообщаем об ошибке, но продолжаем
            output_lines.append(f"ERROR {e.line}:{e.col} {e.message}")
            # пропускаем плохой символ, чтобы не зациклиться
            if scanner.is_at_end():
                break
            scanner._advance()
            continue

        output_lines.append(tok.to_output())
        if tok.kind == TokKind.EOF:
            break

    text = "\n".join(output_lines)

    # либо печатаем, либо пишем в файл
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(text + "\n")
    else:
        print(text)

    return 0


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

    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())