# mini-cc

Учебный компилятор для упрощённого C-like языка.
Разрабатывается по спринтам: лексер, парсер, AST, семантика, IR, оптимизатор, x86-64 кодогенерация.

## Команда

- Студент: Даниил Мартынов
- Группа: (укажи свою группу)
- Курс: (укажи курс)

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

Запустить лексер на примере:

```
py cli.py scan --input examples/hello.src
```

Вывод:

```
1:1 KW_FN "fn"
1:4 IDENT "main"
1:8 LPAREN "("
1:9 RPAREN ")"
1:10 LBRACE "{"
2:5 KW_INT "int"
2:9 IDENT "counter"
2:17 ASSIGN "="
2:19 INT_LIT "42" 42
2:21 SEMI ";"
3:5 KW_RETURN "return"
3:12 INT_LIT "0" 0
3:13 SEMI ";"
4:1 RBRACE "}"
5:1 END_OF_FILE ""
```

## Команды CLI

| Команда | Описание |
|---------|----------|
| `scan` | лексический анализ |
| `tree` | синтаксический анализ (Sprint 2) |
| `check` | семантический анализ (Sprint 3) |
| `ir` | генерация IR (Sprint 4) |
| `codegen` | генерация x86-64 (Sprint 5) |

## Тесты

Запустить все тесты лексера:

```
py tests/test_runner/run_tests.py
```

Ожидаемый вывод:

```
OK   valid/test_comments.src
OK   valid/test_identifiers.src
OK   valid/test_keywords.src
OK   valid/test_numbers.src
OK   valid/test_operators.src
OK   valid/test_strings.src
OK   invalid/test_invalid_char.src
OK   invalid/test_unterminated_comment.src
OK   invalid/test_unterminated_string.src

passed: 9/9
```

## Статус спринтов

- [x] Sprint 1 — Lexer / Scanner
- [ ] Sprint 2 — Parser / AST
- [ ] Sprint 3 — Semantic Analysis
- [ ] Sprint 4 — Intermediate Representation
- [ ] Sprint 5 — x86-64 Code Generation
- [ ] Sprint 6 — Optimizer
- [ ] Sprint 7 — Advanced Features

## Структура проекта

```
mini-cc/
├── src/
│   └── lexer/
│       ├── tok.py          # типы токенов и класс Token
│       ├── scanner.py      # сам сканер
│       └── errors.py       # ScanError
├── tests/
│   ├── lexer/
│   │   ├── valid/          # корректные примеры
│   │   └── invalid/        # примеры с ошибками
│   └── test_runner/
│       └── run_tests.py    # раннер тестов
├── examples/
│   └── hello.src
├── docs/
│   └── language_spec.md    # спецификация языка
├── cli.py                  # точка входа
└── setup.py
```

## Спецификация языка

См. [docs/language_spec.md](docs/language_spec.md).