## 1. Сборка интерпретатора

```powershell
mvn -q package -DskipTests
```

После сборки jar лежит в `target/refal5q.jar`.

## 2. Запуск `.ref`-файла (одного или нескольких)

```powershell
# Один файл
java -jar target/refal5q.jar <путь_к_файлу.ref>

# Несколько файлов — через + (без пробелов)
java -jar target/refal5q.jar main.ref+lib1.ref+lib2.ref
```

Файлы объединяются в единое пространство имён. Функции с `$ENTRY` (публичные) доступны
из любого файла. Функции без `$ENTRY` (приватные) получают уникальный префикс по имени
файла и не видны из других файлов — это предотвращает коллизии между внутренними
хелперами разных модулей.

Опции:

| Опция | Значение |
| --- | --- |
| `--entry Name` | переопределить точку входа (по умолчанию `Go` или то, что указано в `$ENTRY`) |
| `--step-limit N` | ограничить число шагов нормализации (по умолчанию 100 000) |
| `--expr "..."` | передать выражение как аргумент функции входа |

Коды возврата процесса:

| Код | Смысл |
| --- | --- |
| 0 | программа отработала нормально |
| 1 | ошибка парсинга / семантической проверки |
| 2 | runtime-ошибка (RefalException) |
| иной | значение, переданное в `<Exit N>` |

## 3. Запуск рассахаривателя (desugar)

`r5fw-desugar` лежит в `../refal-5-framework-master/bin/`. Это исполняемый
скрипт-обёртка над refgo. Он принимает имя исходника и выводит
рассахаренный текст в файл с суффиксом `_d.ref`.

```powershell
# Один файл
& "..\refal-5-framework-master\bin\r5fw-desugar.cmd" path\to\input.ref

# Можно явно указать выходной файл:
& "..\refal-5-framework-master\bin\r5fw-desugar.cmd" input.ref output_d.ref
```

После выполнения рядом появится `input_d.ref` (или указанный файл).

## 4. Прогон всех рассахаренных автотестов (Сейчас в папке проекта tests)

В `../refal-5-framework-master/bin/desugared_tests/` лежит набор `*.OK_d.ref` —
уже рассахаренные тесты, ожидаемый код возврата 0.

Bash-вариант (Git Bash / WSL):

```bash
jar="target/refal5q.jar"
dir="../refal-5-framework-master/bin/desugared_tests"
pass=0; fail=0
for f in "$dir"/*.OK_d.ref; do
    java -jar "$jar" "$f" </dev/null >/dev/null 2>&1 \
        && pass=$((pass+1)) \
        || { fail=$((fail+1)); echo "FAIL: $(basename "$f")"; }
done
echo "$pass passed, $fail failed"
```

Текущий результат: **29 / 50** OK-тестов проходит (6 пропущено — читают stdin/запускают внешние процессы).
Оставшиеся требуют либо нестандартных встроенных функций
(`Random`, `GetEnv`, `System`, `ExistFile`, `SizeOf`, ...), либо «закопанных»
хранилищ (`Br`, `Cp`, `Dg`, `Dgall`, `Rp`), либо внешних модулей
(`Mu-Residue` — `External-1/2`), либо подачи на stdin/CLI
(`Card`, `Arg`, `Get-*`).

## 5. Тесты на ошибки (`FAIL.ref` и `SYNTAX-ERROR.ref`) (Должны быть в папке tests)

Эти тесты лежат рядом, в `autotests/compatibility/`, без рассахаривания:

- `*.FAIL.ref` должен завершаться с кодом 2 (runtime-ошибка);
- `*.SYNTAX-ERROR.ref` должен завершаться с кодом 1 (ошибка парсинга или семантики).

```bash
jar="target/refal5q.jar"
dir="autotests/compatibility"

# FAIL: ждём exit 2
ok=0; bad=0
for f in "$dir"/*.FAIL.ref; do
    java -jar "$jar" "$f" </dev/null >/dev/null 2>&1
    [ $? -eq 2 ] && ok=$((ok+1)) || { bad=$((bad+1)); echo "WRONG: $(basename "$f")"; }
done
echo "FAIL→exit2: $ok ok, $bad wrong"

# SYNTAX-ERROR: ждём exit 1
ok=0; bad=0
for f in "$dir"/*.SYNTAX-ERROR.ref; do
    java -jar "$jar" "$f" </dev/null >/dev/null 2>&1
    [ $? -eq 1 ] && ok=$((ok+1)) || { bad=$((bad+1)); echo "WRONG: $(basename "$f")"; }
done
echo "SYNTAX-ERROR→exit1: $ok ok, $bad wrong"
```

Текущий результат: **10/10 FAIL** и **30/32 SYNTAX-ERROR** ведут себя как
ожидается.

## 6. Рассахаривание файла через наш интерпретатор
Рассахариватель — это Refal-5 программа, переведённая в базисное подмножество
(файлы `tests/desugar/`). Наш интерпретатор запускает её и скармливает ей
произвольный `.ref`-файл с **расширенным** синтаксом (условия `, e.Cond`,
блоки `{ : }`). Рассахариватель пишет рассахаренную версию в файл рядом с
исходником (суффикс `-out.ref`).

**Шаг 1. Рассахариваем файл с условиями.**

Готовый пример лежит в `tests/multifile/extended.ref`:

```refal
$ENTRY Go {
  = <Prout <Classify 1>>
    <Prout <Classify 2>>
    <Prout <Classify 3>>;
}
Classify {
  s.N, <Compare s.N 2>: '-' = Less;
  s.N, <Compare s.N 2>: '0' = Equal;
  s.N                       = Greater;
}
```

Запускаем рассахариватель через наш интерпретатор:

```
java -jar target/refal5q.jar tests/desugar/desugar_desugared.ref+tests/desugar/LibraryEx_desugared.ref+tests/desugar/R5FW-Parser_desugared.ref+tests/desugar/R5FW-Plainer_desugared.ref+tests/desugar/R5FW-Transformer_desugared.ref --entry Go tests/multifile/extended.ref
```

Результат записывается в `tests/multifile/extended-out.ref` (exit code `0`).

**Шаг 2. Запускаем рассахаренный файл.**

```
java -jar target/refal5q.jar tests/multifile/extended-out.ref
```

Ожидаемый вывод:
```
Less
Equal
Greater
```

**Для других файлов** — тот же вызов, просто замените путь к `.ref`-файлу:

```
java -jar target/refal5q.jar tests/desugar/desugar_desugared.ref+tests/desugar/LibraryEx_desugared.ref+tests/desugar/R5FW-Parser_desugared.ref+tests/desugar/R5FW-Plainer_desugared.ref+tests/desugar/R5FW-Transformer_desugared.ref --entry Go <путь к файлу>
```

## 7. Unit- и интеграционные тесты Maven

```
mvn test
```

## 8. Проверка многофайловой поддержки

Синтаксис: несколько файлов объединяются через `+` без пробелов.  
Файлы готовы в `tests/multifile/`:

```
tests/multifile/main.ref   — $ENTRY Go, вызывает Hello из библиотеки
tests/multifile/lib.ref    — $ENTRY Hello, возвращает 'Hello from lib'
```

**Запуск:**

```
java -jar target/refal5q.jar tests/multifile/main.ref+tests/multifile/lib.ref
```

Ожидаемый вывод: `Hello from lib`, exit code `0`.
