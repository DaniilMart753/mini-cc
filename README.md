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

### Семантический анализ

```
py cli.py check --input examples/valid.src
```

Вывод:

```
OK
```

Если есть ошибка — `ERROR line:col message`.

### Генерация IR

```
py cli.py ir --input examples/ir_simple.src
```

Вывод:

```
func main:
t1 = 2 + 3
x = t1
return x
return
```

## Команды CLI

| Команда | Описание |
|---------|----------|
| `scan` | лексический анализ |
| `tree` | синтаксический анализ |
| `check` | семантический анализ |
| `ir` | генерация IR |
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
OK   semantic/invalid/test_bad_args.src
OK   semantic/invalid/test_bad_condition.src
OK   semantic/invalid/test_bad_return.src
OK   semantic/invalid/test_redeclare.src
OK   semantic/invalid/test_type_mismatch.src
OK   semantic/invalid/test_undefined.src
OK   semantic/valid/test_basic.src
OK   semantic/valid/test_control.src
OK   semantic/valid/test_func_call.src
OK   semantic/valid/test_scopes.src
OK   semantic/valid/test_types.src
OK   ir/valid/test_arithmetic.src
OK   ir/valid/test_call.src
OK   ir/valid/test_func.src
OK   ir/valid/test_if.src
OK   ir/valid/test_if_else.src
OK   ir/valid/test_simple.src
OK   ir/valid/test_while.src

passed: 38/38
```

## Статус спринтов

- [x] Sprint 1 — Lexer / Scanner
- [x] Sprint 2 — Parser / AST
- [x] Sprint 3 — Semantic Analysis
- [x] Sprint 4 — Intermediate Representation
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
│   ├── parser/
│   │   ├── ast_nodes.py    # классы узлов AST
│   │   ├── parser.py       # рекурсивный спуск
│   │   └── errors.py       # ParseError
│   ├── semantic/
│   │   ├── symbol_table.py # таблица символов и scope
│   │   ├── analyzer.py     # семантический анализ
│   │   └── errors.py       # SemanticError
│   └── ir/
│       ├── ir_instructions.py  # классы инструкций IR
│       ├── basic_block.py      # базовый блок
│       ├── control_flow.py     # CFG
│       └── ir_generator.py     # генератор IR из AST
├── tests/
│   ├── lexer/
│   │   ├── valid/
│   │   └── invalid/
│   ├── parser/
│   │   ├── valid/
│   │   └── invalid/
│   ├── semantic/
│   │   ├── valid/
│   │   └── invalid/
│   ├── ir/
│   │   └── valid/
│   └── test_runner/
│       └── run_tests.py
├── examples/
│   ├── hello.src
│   ├── control.src
│   ├── valid.src
│   ├── invalid.src
│   ├── ir_simple.src
│   └── ir_if.src
├── docs/
│   └── language_spec.md
├── cli.py
└── setup.py
```

## Спецификация языка

См. [docs/language_spec.md](docs/language_spec.md).