"""
Generate VKR presentation matching Example.pptx style:
- White background
- Blue header bar (like Example)
- Times New Roman font throughout
- Black text
- Slide numbers bottom-right
- Slide 1: MGTU emblem, university header, bold title center, student/supervisor bottom-right
"""
import os, copy
os.chdir(r'C:\Users\User')  # avoid pptx/inspect name conflict

from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from lxml import etree

# ── constants ──────────────────────────────────────────────────────────────────
HEADER_BLUE = RGBColor(0x1F, 0x56, 0x9E)  # same-ish as Example header
WHITE       = RGBColor(0xFF, 0xFF, 0xFF)
BLACK       = RGBColor(0x00, 0x00, 0x00)
W = Inches(13.33)
H = Inches(7.5)

FONT_MAIN  = "Times New Roman"

# ── helper: make blank slide ───────────────────────────────────────────────────
def new_slide(prs):
    blank = prs.slide_layouts[6]   # blank layout
    return prs.slides.add_slide(blank)

# ── helper: add textbox ────────────────────────────────────────────────────────
def tb(slide, text, left, top, width, height,
       size=20, bold=False, color=BLACK, align=PP_ALIGN.LEFT,
       italic=False, wrap=True, font=FONT_MAIN):
    shape = slide.shapes.add_textbox(left, top, width, height)
    tf = shape.text_frame
    tf.word_wrap = wrap
    para = tf.paragraphs[0]
    para.alignment = align
    _set_run(para, text, size, bold, color, italic, font)
    return shape

def _set_run(para, text, size, bold, color, italic=False, font=FONT_MAIN):
    run = para.add_run()
    run.text = text
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.italic = italic
    run.font.color.rgb = color
    run.font.name = font
    return run

def add_para(tf, text, size=20, bold=False, color=BLACK,
             align=PP_ALIGN.LEFT, indent_lvl=0, font=FONT_MAIN,
             space_before=2, space_after=1):
    para = tf.add_paragraph()
    para.alignment = align
    para.level = indent_lvl
    para.space_before = Pt(space_before)
    para.space_after  = Pt(space_after)
    _set_run(para, text, size, bold, color, font=font)
    return para

def set_first_para(tf, text, size=20, bold=False, color=BLACK,
                   align=PP_ALIGN.LEFT, font=FONT_MAIN):
    para = tf.paragraphs[0]
    para.alignment = align
    _set_run(para, text, size, bold, color, font=font)
    return para

# ── helper: solid rect (no border) ────────────────────────────────────────────
def solid_rect(slide, left, top, width, height, rgb):
    from pptx.util import Emu
    sp = slide.shapes.add_shape(1, left, top, width, height)
    sp.fill.solid()
    sp.fill.fore_color.rgb = rgb
    sp.line.fill.background()
    return sp

# ── helper: slide number ───────────────────────────────────────────────────────
def add_num(slide, n):
    tb(slide, str(n),
       W - Inches(0.8), H - Inches(0.45),
       Inches(0.65), Inches(0.35),
       size=14, color=BLACK, align=PP_ALIGN.RIGHT)

# ── helper: blue header bar + title ───────────────────────────────────────────
def add_header(slide, title):
    # Blue rectangle
    solid_rect(slide, 0, 0, W, Inches(0.75), HEADER_BLUE)
    # White title text over it
    tb(slide, title,
       Inches(0.3), Inches(0.05),
       W - Inches(0.6), Inches(0.68),
       size=24, bold=True, color=WHITE, align=PP_ALIGN.LEFT)

# ── helper: content body textbox ──────────────────────────────────────────────
def body_tf(slide):
    shape = slide.shapes.add_textbox(
        Inches(0.5), Inches(0.9),
        W - Inches(1.0), H - Inches(1.5))
    shape.text_frame.word_wrap = True
    return shape.text_frame

# ═══════════════════════════════════════════════════════════════════════════════
# Build presentation
# ═══════════════════════════════════════════════════════════════════════════════
prs = Presentation()
prs.slide_width  = W
prs.slide_height = H

# ── SLIDE 1: Title ─────────────────────────────────────────────────────────────
s = new_slide(prs)

# University header text (small, centered, top area)
UNIV = (
    "Министерство науки и высшего образования Российской Федерации\n"
    "Федеральное государственное автономное образовательное учреждение высшего образования\n"
    "«Московский государственный технический университет имени Н.Э. Баумана\n"
    "(национальный исследовательский университет)» (МГТУ им. Н.Э. Баумана)"
)

# Emblem image
EMBLEM = r"D:\Programming\Projects\8 Semestr\Diploma\vkr\emblem_no_bg.png"
prs.slides[0].shapes.add_picture(EMBLEM,
    Inches(0.55), Inches(0.22),
    Inches(1.15), Inches(1.3))

# University name text (right of emblem)
shape_univ = s.shapes.add_textbox(Inches(1.85), Inches(0.2), Inches(11.0), Inches(1.5))
tf_univ = shape_univ.text_frame
tf_univ.word_wrap = True
set_first_para(tf_univ, UNIV, size=11, color=BLACK, align=PP_ALIGN.CENTER)

# Main title (large, bold, centered, ~middle of slide)
shape_title = s.shapes.add_textbox(Inches(0.8), Inches(2.3), Inches(11.7), Inches(2.2))
tf_title = shape_title.text_frame
tf_title.word_wrap = True
p = tf_title.paragraphs[0]
p.alignment = PP_ALIGN.CENTER
_set_run(p,
    "Реализация базисного подмножества Рефала-5\n"
    "с использованием раскрученных двусторонних очередей",
    size=32, bold=True, color=BLACK)

# Subtitle "Выпускная квалификационная работа"
shape_sub = s.shapes.add_textbox(Inches(0.8), Inches(4.55), Inches(11.7), Inches(0.55))
tf_sub = shape_sub.text_frame
set_first_para(tf_sub,
    "Выпускная квалификационная работа",
    size=18, bold=False, color=BLACK, align=PP_ALIGN.CENTER)

# Student / supervisor (bottom right)
shape_info = s.shapes.add_textbox(Inches(6.5), Inches(5.3), Inches(6.4), Inches(1.1))
tf_info = shape_info.text_frame
tf_info.word_wrap = True
p = tf_info.paragraphs[0]
p.alignment = PP_ALIGN.RIGHT
_set_run(p, "Выполнил: Аринин М. А., ИУ9-82Б", size=18, bold=False, color=BLACK)
p2 = tf_info.add_paragraph()
p2.alignment = PP_ALIGN.RIGHT
_set_run(p2, "Руководитель: Коновалов А. В.", size=18, bold=False, color=BLACK)

add_num(s, 1)

# ── Slides 2–15: content ───────────────────────────────────────────────────────

INDENT_EMU = int(Inches(0.45))   # left indent for sub-items (level=1)

def _set_para_indent(para, level):
    """Set left margin via XML pPr to avoid inheriting theme font sizes."""
    from lxml import etree
    nsmap = "http://schemas.openxmlformats.org/drawingml/2006/main"
    pPr = para._p.get_or_add_pPr()
    if level == 1:
        pPr.set("marL", str(INDENT_EMU))
        pPr.set("indent", "0")
    else:
        # remove any inherited indent
        pPr.attrib.pop("marL", None)
        pPr.attrib.pop("indent", None)

def make_content_slide(prs, num, title, items):
    """
    items: list of (text, level, bold)
      level 0 = normal line, level 1 = indented sub-line (same font size)
      Empty string = blank spacer line
    """
    s = new_slide(prs)
    add_header(s, title)
    tf = body_tf(s)
    first = True
    for (text, level, bold) in items:
        size = 20   # uniform size — no inheritance tricks
        color = BLACK
        if first:
            p = tf.paragraphs[0]
            p.alignment = PP_ALIGN.LEFT
            p.space_before = Pt(3 if text != "" else 6)
            p.space_after  = Pt(1)
            _set_para_indent(p, level)
            _set_run(p, text, size, bold, color)
            first = False
        else:
            p = tf.add_paragraph()
            p.alignment = PP_ALIGN.LEFT
            p.space_before = Pt(1 if text != "" else 5)
            p.space_after  = Pt(1)
            _set_para_indent(p, level)
            _set_run(p, text, size, bold, color)
    add_num(s, num)
    return s

# ── SLIDE 2 ───────────────────────────────────────────────────────────────────
make_content_slide(prs, 2, "Цель и объект исследования", [
    ("Объект исследования:",                                         0, True),
    ("Программная система трансляции и исполнения программ",         1, False),
    ("на базисном подмножестве языка Рефал-5",                       1, False),
    ("",                                                             0, False),
    ("Цель работы:",                                                 0, True),
    ("Разработать компилятор базисного подмножества Рефала-5,",      1, False),
    ("использующий раскрученную двустороннюю очередь",               1, False),
    ("для представления объектных выражений",                        1, False),
    ("",                                                             0, False),
    ("Подтвердить корректность и работоспособность реализации",      1, False),
    ("автоматическими тестами и сравнительным замером",              1, False),
    ("производительности",                                           1, False),
])

# ── SLIDE 3 ───────────────────────────────────────────────────────────────────
make_content_slide(prs, 3, "Задачи работы", [
    ("1. Изучить базовые конструкции и терминологию языка Рефал-5",  0, False),
    ("2. Исследовать существующие представления объектных выражений", 0, False),
    ("   и обсудить их компромиссы по ключевым операциям",           1, False),
    ("3. Обосновать выбор раскрученной двусторонней очереди",        0, False),
    ("   как представления, амортизированно покрывающего все",       1, False),
    ("   основные операции",                                         1, False),
    ("4. Спроектировать архитектуру: состав модулей, интерфейсы,",   0, False),
    ("   форматы диагностических сообщений",                         1, False),
    ("5. Реализовать компилятор на платформе JVM (Java 25 LTS)",     0, False),
    ("6. Построить автоматический набор тестов и провести",          0, False),
    ("   сравнительный прогон с двумя альтернативными реализациями", 1, False),
])

# ── SLIDE 4 ───────────────────────────────────────────────────────────────────
make_content_slide(prs, 4, "Язык Рефал-5: основные понятия", [
    ("Программа — набор функций",                                    0, False),
    ("Функция — предложения вида «образец = результат»",             0, False),
    ("При вызове: первое подходящее правило просматривается сверху вниз", 0, False),
    ("",                                                             0, False),
    ("Переменные образца:",                                          0, True),
    ("s.X  —  один символ (атомарный терм)",                         1, False),
    ("t.X  —  один терм (в том числе скобочный)",                    1, False),
    ("e.X  —  цепочка термов произвольной длины",                    1, False),
    ("",                                                             0, False),
    ("Ключевые операции при исполнении:",                            0, True),
    ("• Отделение терма с начала / с конца выражения",               1, False),
    ("• Конкатенация двух выражений",                                1, False),
    ("• Повторное использование значения переменной",                1, False),
])

# ── SLIDE 5 ───────────────────────────────────────────────────────────────────
make_content_slide(prs, 5, "Представления объектных выражений", [
    ("Классическое (плоское двусвязное):",                           0, True),
    ("+ O(1) на концах,  + O(1) конкатенация,  − O(N) копирование", 1, False),
    ("",                                                             0, False),
    ("Компромиссное (подвешенные скобки):",                          0, True),
    ("+ снижает копирование до верхнего уровня",                     1, False),
    ("− сложное управление памятью (счётчики ссылок)",               1, False),
    ("",                                                             0, False),
    ("Массивное (с дырками):",                                       0, True),
    ("+ O(1) копирование переменной,  − конкатенация O(|X|+|Y|)",   1, False),
    ("",                                                             0, False),
    ("Дерево конкатенаций (rope):",                                  0, True),
    ("+ O(1) конкатенация и копирование",                            1, False),
    ("− O(log N) операции на концах — дорого для e-переменных",      1, False),
    ("",                                                             0, False),
    ("Вывод: ни одно представление не покрывает все три требования", 0, True),
])

# ── SLIDE 6 ───────────────────────────────────────────────────────────────────
make_content_slide(prs, 6, "Выбранное представление: раскрученная двусторонняя очередь", [
    ("Структура по Окасаки — два уровня вложенности:",               0, True),
    ("",                                                             0, False),
    ("Мелкий уровень (ShallowDeque):",                               0, True),
    ("Циклический массив, CAPACITY = 9",                             1, False),
    ("Операции на концах — сдвиг индексов, строго O(1)",             1, False),
    ("",                                                             0, False),
    ("Глубокий уровень (DeepDeque):",                                0, True),
    ("Тройка ⟨front, mid, back⟩: крайние — мелкие буферы,",         1, False),
    ("mid — очередь мелких буферов (рекурсивно)",                    1, False),
    ("Инвариант: буферы mid заполнены не менее чем наполовину",      1, False),
    ("",                                                             0, False),
    ("Амортизированные оценки:",                                     0, True),
    ("Отделение терма с конца — O(1),  Конкатенация — O(1)",         1, False),
    ("Повторное использование переменной — O(1) (структурное разделение)", 1, False),
])

# ── SLIDE 7 ───────────────────────────────────────────────────────────────────
make_content_slide(prs, 7, "Архитектура системы", [
    ("Цепочка трансляции:",                                          0, True),
    ("Исходный текст → Лексер → Парсер → Семантика → Исполнение",    1, False),
    ("",                                                             0, False),
    ("Модули (Java-пакеты):",                                        0, True),
    ("refal.deque    — Expr<T>, ShallowDeque, DeepDeque, ExprOps",   1, False),
    ("refal.ast      — Term, Var, Br, Call, Rule, Func, Program",    1, False),
    ("refal.lexer    — Lexer, Token, LexException",                  1, False),
    ("refal.parser   — Parser, ParseException",                      1, False),
    ("refal.semantic — SemanticChecker, SemanticException",          1, False),
    ("refal.runtime  — Matcher, Substitutor, Runtime, Builtins",     1, False),
    ("refal.Main     — интерфейс командной строки",                  1, False),
    ("",                                                             0, False),
    ("Внешний рассахариватель r5fw-desugar:",                        0, True),
    ("Переводит расширенный синтаксис к базисному подмножеству;",    1, False),
    ("интерпретатор принимает его результат без изменений ядра",     1, False),
])

# ── SLIDE 8 ───────────────────────────────────────────────────────────────────
make_content_slide(prs, 8, "Ключевые решения реализации", [
    ("Sealed interface Expr<T>:",                                    0, True),
    ("Два наследника: ShallowDeque<T> и DeepDeque<T>",               1, False),
    ("Компилятор Java 25 проверяет полноту switch — default не нужна", 1, False),
    ("",                                                             0, False),
    ("Конкатенация (ExprOps.concat) — четыре случая:",               0, True),
    ("Shallow+Shallow, Shallow+Deep, Deep+Shallow, Deep+Deep",       1, False),
    ("Рекурсивное слияние mid-очередей, O(1) амортизированно",       1, False),
    ("",                                                             0, False),
    ("Оптимизация BulkPassive: O(N²) → O(N)",                       0, True),
    ("Без: подстановка переменной = N вызовов pushFront",            1, False),
    ("С:   всё значение — один объект BulkPassive на стек",          1, False),
    ("При сборке аргументов: Expr.concat(bp.items(), argsExpr) — O(1) аморт.", 1, False),
])

# ── SLIDE 9 ───────────────────────────────────────────────────────────────────
make_content_slide(prs, 9, "Цикл нормализации", [
    ("Двустековая схема:",                                           0, True),
    ("right — необработанные элементы поля зрения",                 1, False),
    ("left  — пассивные (уже нормализованные) элементы",            1, False),
    ("",                                                             0, False),
    ("Единицы поля зрения (ViewTerm):",                              0, True),
    ("Passive / BulkPassive  — пассивные термы",                     1, False),
    ("AngOpen(fn) / AngClose — маркеры вызова функции",              1, False),
    ("ParenOpen / ParenClose — маркеры скобочного терма",            1, False),
    ("",                                                             0, False),
    ("Шаг при встрече AngClose:",                                    0, True),
    ("1. Снять с left элементы до парного AngOpen",                  1, False),
    ("2. Собрать argsExpr через concat — O(1) амортизированно",      1, False),
    ("3. Встроенная функция → выполнить примитив → в right",         1, False),
    ("4. Пользовательская → найти правило, подставить → в right",   1, False),
    ("",                                                             0, False),
    ("Итеративность — независимость от глубины JVM-стека",           0, False),
])

# ── SLIDE 10 ──────────────────────────────────────────────────────────────────
make_content_slide(prs, 10, "Стратегия и состав тестирования", [
    ("Три уровня:",                                                  0, True),
    ("",                                                             0, False),
    ("Юнит-тесты — компоненты в изоляции:",                         0, False),
    ("ShallowDeque, DeepDeque, ExprOps.concat",                      1, False),
    ("Лексер, парсер, семантика; Matcher, Substitutor, Builtins",    1, False),
    ("",                                                             0, False),
    ("Интеграционные тесты:",                                        0, False),
    ("Полная цепочка «разбор → семантика → нормализация»",           1, False),
    ("Проверка вывода и кодов возврата CLI",                         1, False),
    ("",                                                             0, False),
    ("Совместимостные тесты (AutotestsRunnerTest):",                 0, False),
    ("Интерпретатор запускается как внешний процесс",                1, False),
    ("81 программа из refal-5j и refal-5-framework",                 1, False),
    ("Таймаут 20 секунд на программу",                               1, False),
    ("",                                                             0, False),
    ("Итого: 224 теста.  Инструменты: JUnit 5, AssertJ, JaCoCo",    0, True),
])

# ── SLIDE 11 ──────────────────────────────────────────────────────────────────
make_content_slide(prs, 11, "Результаты тестирования", [
    ("mvn test: 224 / 224  ✓",                                       0, True),
    ("",                                                             0, False),
    ("MUST_PASS-программы:",                                         0, True),
    ("refal-5j:    5 из 5  — пройдены все обязательные",             1, False),
    ("desugared:  18 из 18 — пройдены все обязательные",             1, False),
    ("",                                                             0, False),
    ("Покрытие кода (JaCoCo):",                                      0, True),
    ("refal.deque:      86,7 % инструкций  /  72,9 % ветки",        1, False),
    ("refal.lexer:      90,3 % инструкций  /  80,9 % ветки",        1, False),
    ("refal.parser:     86,5 % инструкций  /  76,1 % ветки",        1, False),
    ("refal.semantic:   94,8 % инструкций  /  95,5 % ветки",        1, False),
    ("refal.runtime:    85,6 % инструкций  /  74,7 % ветки",        1, False),
    ("Итого по проекту: 87,3 % инструкций  /  76,9 % ветки",        1, True),
    ("",                                                             0, False),
    ("Пороги pom.xml (≥70 % инструкций, ≥55 % ветки) — превышены",  0, False),
])

# ── SLIDE 12 — two-column: text left, graph right ────────────────────────────
s12 = new_slide(prs)
add_header(s12, "Сравнительный прогон: Loop/Select")

# Left text column
GRAPH_PNG = r"D:\Programming\Projects\8 Semestr\Diploma\presentation\loop-select-graph.png"
TEXT_W = Inches(5.9)
shape12 = s12.shapes.add_textbox(Inches(0.35), Inches(0.9), TEXT_W, H - Inches(1.3))
shape12.text_frame.word_wrap = True
tf12 = shape12.text_frame

items12 = [
    ("Синтетический тест: N итераций с растущим аккумулятором e.Acc", 0, False),
    ("На каждом шаге e.Acc используется в двух аргументах",           0, False),
    ("",                                                              0, False),
    ("Ожидаемые сложности:",                                          0, True),
    ("Список (PZ, R5J):  O(N²) — копирование e.Acc",                  1, False),
    ("Раскрученная очередь (наша):  O(N)",                            1, False),
    ("",                                                              0, False),
    ("Результаты (медиана 3 прогонов, мс):",                          0, True),
    ("N=10 000:  наша 254,   PZ  277,   R5J  440",                    1, False),
    ("N=15 000:  наша 297,   PZ  632,   R5J  830",                    1, False),
    ("N=20 000:  наша 302,   PZ 1059,   R5J 1348",                    1, True),
    ("",                                                              0, False),
    ("При N=20 000:",                                                 0, True),
    ("PZ в 3,5 раза медленнее нашей",                                 1, False),
    ("R5J в 4,5 раза медленнее нашей",                                1, False),
]
first = True
for (text, level, bold) in items12:
    size = 18
    if first:
        p = tf12.paragraphs[0]
        p.space_before = Pt(3 if text != "" else 6)
        p.space_after  = Pt(1)
        _set_para_indent(p, level)
        _set_run(p, text, size, bold, BLACK)
        first = False
    else:
        p = tf12.add_paragraph()
        p.space_before = Pt(1 if text != "" else 4)
        p.space_after  = Pt(1)
        _set_para_indent(p, level)
        _set_run(p, text, size, bold, BLACK)

# Right: graph image
IMG_LEFT = Inches(6.4)
IMG_TOP  = Inches(0.9)
IMG_W    = W - IMG_LEFT - Inches(0.2)
IMG_H    = H - IMG_TOP - Inches(0.5)
s12.shapes.add_picture(GRAPH_PNG, IMG_LEFT, IMG_TOP, IMG_W, IMG_H)

add_num(s12, 12)

# ── SLIDE 13 ──────────────────────────────────────────────────────────────────
make_content_slide(prs, 13, "Сравнительный прогон: рассахариватель", [
    ("Реальная программа: рассахариватель refal-5-framework",        0, False),
    ("5 модулей, ~4200 строк; вход: R5FW-Parser.ref (1038 строк)",   1, False),
    ("Ожидаемый выход: 1631 строка",                                 1, False),
    ("",                                                             0, False),
    ("Способы исполнения:",                                          0, True),
    ("refal5q-impl — интерпретация рассахаренных .ref-файлов",       1, False),
    ("Refal-5 PZ   — компиляция (refc) + исполнение (refgo)",        1, False),
    ("Refal-5J     — компиляция (r5jc + javac) + исполнение",        1, False),
    ("",                                                             0, False),
    ("Результаты (медиана 3 прогонов):",                             0, True),
    ("refal5q-impl:  2055 мс  (интерпретация)",                      1, False),
    ("Refal-5 PZ:     369 мс  (компиляция, ×5,6 быстрее)",          1, False),
    ("Refal-5J:      1632 мс  (компиляция, ×1,3 быстрее)",          1, False),
    ("",                                                             0, False),
    ("Все три реализации дают эквивалентный выход (1631 строка)",    0, True),
    ("Разница — компиляция vs интерпретация, не структура данных",   1, False),
])

# ── SLIDE 14 ──────────────────────────────────────────────────────────────────
make_content_slide(prs, 14, "Выводы", [
    ("1. Рассмотрены пять представлений объектных выражений;",       0, False),
    ("   обоснован выбор раскрученной двусторонней очереди по Окасаки", 1, False),
    ("",                                                             0, False),
    ("2. Разработан компилятор базисного подмножества Рефала-5",     0, False),
    ("   (Maven-проект refal5q-impl, ~3500 строк основного кода)",   1, False),
    ("",                                                             0, False),
    ("3. Построен автоматический набор из 224 тестов;",              0, False),
    ("   покрытие 87,3 % инструкций / 76,9 % ветки",                 1, False),
    ("",                                                             0, False),
    ("4. Синтетический прогон Loop/Select подтвердил O(N) против O(N²);", 0, False),
    ("   при N = 20 000 выигрыш 3,5–4,5 раза",                       1, False),
    ("",                                                             0, False),
    ("5. Прогон рассахаривателя подтвердил корректность",            0, False),
    ("   на реальной программе в 4200 строк",                        1, False),
])

# ── SLIDE 15 ──────────────────────────────────────────────────────────────────
make_content_slide(prs, 15, "Направления дальнейшего развития", [
    ("1. Компиляция в JVM-байт-код:",                                0, True),
    ("Порождение отдельного Java-метода для каждого правила",         1, False),
    ("Снизит постоянный множитель, устранит разрыв с R5J",           1, False),
    ("на задачах без квадратичного паттерна",                        1, False),
    ("",                                                             0, False),
    ("2. Поддержка модульной системы Рефала-5:",                     0, True),
    ("Директива *$FROM, квалифицированные имена функций",            1, False),
    ("Сейчас поддерживается конкатенация файлов через +,",           1, False),
    ("но не полноценная модульная система",                          1, False),
    ("",                                                             0, False),
    ("3. Расширение библиотеки встроенных функций:",                 0, True),
    ("Br/Dg, шифр-функции, файловый ввод/вывод",                    1, False),
    ("Архитектура регистрации допускает это без изменений ядра",     1, False),
    ("",                                                             0, False),
    ("",                                                             0, False),
    ("Доклад окончен. Спасибо за внимание.",                         0, True),
])

# ── save ───────────────────────────────────────────────────────────────────────
OUT = r"D:\Programming\Projects\8 Semestr\Diploma\presentation\presentation.pptx"
prs.save(OUT)
print(f"Saved: {OUT}")
print(f"Slides: {len(prs.slides)}")
