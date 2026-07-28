# refal5q-impl — интерпретатор базисного подмножества Рефала-5

Реализация интерпретатора базисного подмножества Рефала-5 на Java 25,
использующая bootstrapped deque (раскрученную двустороннюю очередь по Окасаки)
для представления объектных выражений.

## Требования

- Java 25
- Apache Maven 3.9+

## Сборка

Из папки `refal5q-impl`:

```powershell
mvn -q package -DskipTests
```

Результат: `target/refal5q.jar`.

## Запуск программы

```powershell
java -jar target/refal5q.jar <файл.ref>
```

Несколько файлов объединяются через `+` без пробелов:

```powershell
java -jar target/refal5q.jar main.ref+lib.ref
```

Опции:

| Опция | Значение |
| --- | --- |
| `--entry Name` | переопределить точку входа (по умолчанию `Go`) |
| `--step-limit N` | ограничить число шагов нормализации (по умолчанию 100 000) |
| `--expr "..."` | передать выражение как аргумент функции входа |

Коды возврата: `0` — успех, `1` — ошибка парсинга/семантики, `2` — runtime-ошибка.

## Тесты

```powershell
mvn test
```

Запускает 224 теста: юнит-тесты (deque, лексер, парсер, семантика, runtime),
интеграционные тесты и тесты совместимости на 81 `.ref`-файле.

## Рассахариватель

Файлы рассахаривателя в базисном подмножестве лежат в `tests/desugar/`.
Пример запуска — рассахариваем `tests/multifile/extended.ref` (содержит
условия `, e.Cond` и блоки `{ : }`):

```powershell
java -jar target/refal5q.jar `
  tests/desugar/desugar_desugared.ref+tests/desugar/LibraryEx_desugared.ref+tests/desugar/R5FW-Parser_desugared.ref+tests/desugar/R5FW-Plainer_desugared.ref+tests/desugar/R5FW-Transformer_desugared.ref `
  --entry Go tests/multifile/extended.ref
```

Результат записывается в `tests/multifile/extended-out.ref`.

Запускаем рассахаренный файл:

```powershell
java -jar target/refal5q.jar tests/multifile/extended-out.ref
```

Ожидаемый вывод:
```
Less
Equal
Greater
```

## Структура папок

```
src/main/java/refal/
    ast/        — AST-узлы (Term, Var, Sym, Num, Str, Br, Call, Rule, Func, Program)
    deque/      — Expr<T> (sealed interface), ShallowDeque, DeepDeque, ExprOps
    lexer/      — Lexer
    parser/     — Parser (полная EBNF-грамматика базисного подмножества)
    runtime/    — Runtime, Matcher, Substitutor, Bindings, Builtins
    semantic/   — SemanticChecker

tests/
    autotests/  — тесты из refal-5j (совместимость)
    desugared/  — рассахаренные тесты из refal-5-framework
    desugar/    — файлы рассахаривателя в базисном подмножестве
    multifile/  — примеры многофайловой поддержки

bench/
    *.ps1       — PowerShell-скрипты бенчмарков (сравнение с Refal-5 PZ и Refal-5J)
    *.ref       — тестовые Refal-программы для бенчмарков
    *.csv       — результаты замеров
```
