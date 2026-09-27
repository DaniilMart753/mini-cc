# Language Specification — mini-cc

Спецификация упрощённого C-like языка, для которого мы пишем компилятор.

## 1. Кодировка

Исходный код хранится в **UTF-8**. Поддерживаются Unix (`\n`) и Windows (`\r\n`) переводы строк.

## 2. Ключевые слова

Следующие слова зарезервированы и не могут использоваться как идентификаторы:

```
if, else, while, for, int, float, bool, return, true, false, void, struct, fn
```

## 3. Идентификаторы

Идентификатор — это имя переменной, функции или структуры.

Правила:
- Начинается с буквы `[a-zA-Z]` или подчёркивания `_`
- Продолжается буквами, цифрами `[0-9]` или подчёркиваниями
- Максимальная длина — **255** символов
- Регистрозависимый (`foo` и `Foo` — разные идентификаторы)

EBNF:
```
identifier = ( letter | "_" ) , { letter | digit | "_" } ;
letter     = "a" .. "z" | "A" .. "Z" ;
digit      = "0" .. "9" ;
```

## 4. Литералы

### 4.1 Целые числа

Десятичные цифры. Диапазон: `[-2^31, 2^31 - 1]`.

EBNF:
```
integer = digit , { digit } ;
```

Примеры: `0`, `42`, `2147483647`.

### 4.2 Вещественные числа

Целая часть, точка, дробная часть.

EBNF:
```
float = digit , { digit } , "." , digit , { digit } ;
```

Примеры: `3.14`, `0.5`, `100.0`.

**Важно:** точка **должна** сопровождаться хотя бы одной цифрой. `5.foo` — это не float, а `5`, `.`, `foo`.

### 4.3 Строки

Двойные кавычки. Внутри — любые символы, кроме `"` и `\n`.

Escape-последовательности:
- `\n` — перевод строки
- `\t` — табуляция
- `\\` — обратный слэш
- `\"` — двойная кавычка

EBNF:
```
string = '"' , { character | escape } , '"' ;
escape = "\\" , ( "n" | "t" | "\\" | '"' ) ;
```

Примеры: `"hello"`, `"with \"escape\""`, `"tab\there"`.

### 4.4 Булевы значения

`true` или `false`.

## 5. Операторы

### Арифметические

| Оператор | Токен | Описание |
|----------|-------|----------|
| `+` | `PLUS` | сложение |
| `-` | `MINUS` | вычитание |
| `*` | `STAR` | умножение |
| `/` | `SLASH` | деление |
| `%` | `PERCENT` | остаток |

### Сравнения

| Оператор | Токен |
|----------|-------|
| `==` | `EQ_EQ` |
| `!=` | `NOT_EQ` |
| `<` | `LT` |
| `<=` | `LT_EQ` |
| `>` | `GT` |
| `>=` | `GT_EQ` |

### Логические

| Оператор | Токен |
|----------|-------|
| `&&` | `AND_AND` |
| `\|\|` | `OR_OR` |
| `!` | `BANG` |

### Присваивание

| Оператор | Токен |
|----------|-------|
| `=` | `ASSIGN` |
| `+=` | `PLUS_EQ` |
| `-=` | `MINUS_EQ` |
| `*=` | `STAR_EQ` |
| `/=` | `SLASH_EQ` |

## 6. Разделители

| Символ | Токен | Описание |
|--------|-------|----------|
| `(` | `LPAREN` | левая скобка |
| `)` | `RPAREN` | правая скобка |
| `{` | `LBRACE` | левая фигурная |
| `}` | `RBRACE` | правая фигурная |
| `[` | `LBRACKET` | левая квадратная |
| `]` | `RBRACKET` | правая квадратная |
| `;` | `SEMI` | точка с запятой |
| `,` | `COMMA` | запятая |
| `:` | `COLON` | двоеточие |
| `->` | `ARROW` | стрелка |

## 7. Пробелы и комментарии

### Пробельные символы

- пробел (` `), табуляция (`\t`), перевод строки (`\n`), возврат каретки (`\r`)

Все пробельные символы игнорируются (кроме строк).

### Комментарии

**Однострочные** — от `//` до конца строки:

```
x = 1; // это комментарий
```

**Многострочные** — от `/*` до `*/`:

```
/* это
   многострочный
   комментарий */
```

Вложенность не поддерживается.

## 8. Формат вывода токенов

```
LINE:COLUMN TOKEN_TYPE "LEXEME" [LITERAL_VALUE]
```

Пример:

```
1:1 KW_FN "fn"
1:4 IDENT "main"
```

- `LINE` и `COLUMN` начинаются с **1**
- `LITERAL_VALUE` только для литералов
- `LEXEME` для `END_OF_FILE` пустой

## 9. Ошибки

```
ERROR LINE:COLUMN message
```

Виды ошибок:

- `unexpected character 'X'` — неизвестный символ
- `unterminated string` — строка не закрыта
- `unterminated comment` — комментарий не закрыт
- `identifier too long (max 255)`
- `integer literal out of range`

## 10. Грамматика

Полная грамматика языка в EBNF.

### Верхний уровень

```
program     = { top_level } ;
top_level   = func_decl | struct_decl ;

func_decl   = "fn" , identifier , "(" , [ param_list ] , ")" ,
              [ "->" , type ] , block ;

param_list  = param , { "," , param } ;
param       = type , identifier ;

struct_decl = "struct" , identifier , "{" ,
              { type , identifier , ";" } , "}" ;

type        = "int" | "float" | "bool" | "void" | "struct" | identifier ;
```

### Операторы

```
block       = "{" , { statement } , "}" ;

statement   = block
            | var_decl
            | if_stmt
            | while_stmt
            | for_stmt
            | return_stmt
            | expr_stmt ;

var_decl    = type , identifier , [ "=" , expr ] , ";" ;

if_stmt     = "if" , "(" , expr , ")" , block_or_stmt ,
              [ "else" , block_or_stmt ] ;

while_stmt  = "while" , "(" , expr , ")" , block_or_stmt ;

for_stmt    = "for" , "(" , [ for_init ] , ";" , [ expr ] , ";" , [ expr ] , ")" ,
              block_or_stmt ;

for_init    = var_decl_no_semi | expr ;

return_stmt = "return" , [ expr ] , ";" ;

expr_stmt   = expr , ";" ;

block_or_stmt = block | statement ;
```

### Выражения

```
expr        = assignment ;
assignment  = or_expr , [ assign_op , assignment ] ;
assign_op   = "=" | "+=" | "-=" | "*=" | "/=" ;

or_expr     = and_expr , { "||" , and_expr } ;
and_expr    = eq_expr , { "&&" , eq_expr } ;
eq_expr     = cmp_expr , { ( "==" | "!=" ) , cmp_expr } ;
cmp_expr    = add_expr , { ( "<" | "<=" | ">" | ">=" ) , add_expr } ;
add_expr    = mul_expr , { ( "+" | "-" ) , mul_expr } ;
mul_expr    = unary , { ( "*" | "/" | "%" ) , unary } ;
unary       = ( "-" | "!" ) , unary | primary ;
primary     = int_lit | float_lit | string_lit | bool_lit
            | identifier , [ "(" , [ arg_list ] , ")" ]
            | "(" , expr , ")" ;

arg_list    = expr , { "," , expr } ;
```

**Приоритет операторов** (от слабого к сильному):
1. `=` `+=` `-=` `*=` `/=` (правоассоциативные)
2. `||`
3. `&&`
4. `==` `!=`
5. `<` `<=` `>` `>=`
6. `+` `-`
7. `*` `/` `%`
8. `-` `!` (унарные)
9. вызов, скобки

**Ассоциативность:**
- бинарные арифметические и логические — **левоассоциативные**
- присваивание — **правоассоциативное**