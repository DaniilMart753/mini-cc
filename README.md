# mini-cc

Учебный компилятор для упрощённого C-like языка.
Разрабатывается по спринтам: лексер, парсер, AST, семантика, IR, оптимизатор, x86-64 кодогенерация.

## Команда

- Студент: Даниил Мартынов
- Группа: (впиши свою группу)
- Курс: (впиши свой курс)

## Требования

- Python 3.8+
- Никаких внешних зависимостей

## Сборка

Проект на чистом Python, собирать нечего.
Достаточно склонировать репозиторий:

```
git clone https://github.com/DaniilMart753/mini-cc.git
cd mini-cc
```

## Быстрый старт

### Лексический анализ

```
py cli.py scan --input examples/hello.src
```

### Синтаксический анализ

```
py cli.py tree --input examples/control.src
```

Вывод:

```
Program
  FuncDecl name=main () -> void
    Block
      VarDecl type=int name=x
        IntLit 10
      If
        cond:
          BinOp >
            Ident x
            IntLit 5
        then:
          Block
            Return
              Ident x
        else:
          Block
            Return
              IntLit 0
```

## Команды CLI

| Команда | Описание |
|---------|----------|
| `scan` | лексический анализ |
| `tree` | синтаксический анализ |
| `check` | семантический анализ (Sprint 3) |
| `ir` | генерация IR (Sprint 4) |
| `codegen` | генерация x86-64 (Sprint 5) |

## Тесты

Запустить все тесты:

```
py tests/test_runner/run_tests.py
```

Ожидаемый вывод:

```
OK   lexer/invalid/test_invalid_char.src
OK   lexer/invalid/test_unterminated_comment.src
OK   lexer/invalid/test_unterminated_string.src
OK   lexer/valid/test_comments.src
OK   lexer/valid/test_identifiers.src
OK   lexer/valid/test_keywords.src
OK   lexer/valid/test_numbers.src
OK   lexer/valid/test_operators.src
OK   lexer/valid/test_strings.src
OK   parser/invalid/test_bad_expr.src
OK   parser/invalid/test_missing_rparen.src
OK   parser/invalid/test_missing_semi.src
OK   parser/valid/test_call.src
OK   parser/valid/test_expr.src
OK   parser/valid/test_for.src
OK   parser/valid/test_func.src
OK   parser/valid/test_if.src
OK   parser/valid/test_struct.src
OK   parser/valid/test_var.src
OK   parser/valid/test_while.src

passed: 20/20
```

## Статус спринтов

- [x] Sprint 1 — Lexer / Scanner
- [x] Sprint 2 — Parser / AST
- [ ] Sprint 3 — Semantic Analysis
- [ ] Sprint 4 — Intermediate Representation
- [ ] Sprint 5 — x86-64 Code Generation
- [ ] Sprint 6 — Optimizer
- [ ] Sprint 7 — Advanced Features

## Структура проекта

```
mini-cc/
├── src/
│   ├── lexer/
│   │   ├── tok.py          # типы токенов и класс Token
│   │   ├── scanner.py      # сам сканер
│   │   └── errors.py       # ScanError
│   └── parser/
│       ├── ast_nodes.py    # классы узлов AST
│       ├── parser.py       # рекурсивный спуск
│       └── errors.py       # ParseError
├── tests/
│   ├── lexer/
│   │   ├── valid/
│   │   └── invalid/
│   ├── parser/
│   │   ├── valid/
│   │   └── invalid/
│   └── test_runner/
│       └── run_tests.py
├── examples/
│   ├── hello.src
│   └── control.src
├── docs/
│   └── language_spec.md
├── cli.py
└── setup.py
```

## Спецификация языка

См. [docs/language_spec.md](docs/language_spec.md).