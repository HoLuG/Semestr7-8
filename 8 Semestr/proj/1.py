from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib import colors
import os, textwrap

# Register a font that supports Cyrillic
font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
pdfmetrics.registerFont(TTFont("DejaVuSans", font_path))
pdfmetrics.registerFont(TTFont("DejaVuSans-Bold", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"))

pdf_path = "/mnt/data/Matvey_Arinin_CV.pdf"
c = canvas.Canvas(pdf_path, pagesize=A4)
width, height = A4

left = 18*mm
right = width - 18*mm
y = height - 18*mm

def draw_text(text, font="DejaVuSans", size=11, leading=14, bold=False, space_after=6):
    global y
    c.setFont(font, size)
    max_width = right - left
    lines = []
    for para in text.split("\n"):
        if not para.strip():
            lines.append("")
            continue
        wrapped = textwrap.wrap(para, width=95)
        lines.extend(wrapped)
    for line in lines:
        c.drawString(left, y, line)
        y -= leading
    y -= space_after

def section(title):
    global y
    c.setFont("DejaVuSans-Bold", 13)
    c.drawString(left, y, title)
    y -= 18

def bullet_line(text, size=11):
    global y
    c.setFont("DejaVuSans", size)
    c.drawString(left+8, y, u"\u2022")
    wrapped = textwrap.wrap(text, width=92)
    if wrapped:
        c.drawString(left+18, y, wrapped[0])
        y -= 14
        for cont in wrapped[1:]:
            c.drawString(left+18, y, cont)
            y -= 14
    else:
        y -= 14

# Header
c.setFont("DejaVuSans-Bold", 18)
c.drawString(left, y, "Матвей Аринин")
y -= 22

c.setFont("DejaVuSans", 11)
c.drawString(left, y, "Студент ML / Applied Machine Learning")
y -= 16
c.drawString(left, y, "GitHub: https://github.com/HoLuG/NeuralNetworks")
y -= 18

section("Образование")
c.setFont("DejaVuSans-Bold", 11)
c.drawString(left, y, "МГТУ им. Н.Э. Баумана")
y -= 14
c.setFont("DejaVuSans", 11)
c.drawString(left, y, "Прикладная математика и информатика — 4 курс")
y -= 16

c.setFont("DejaVuSans-Bold", 11)
c.drawString(left, y, "VK Education — «Основы машинного обучения» (синхронный курс)")
y -= 14
c.setFont("DejaVuSans", 11)
edu_text = ("Ключевые темы: ML (линейные модели, деревья и ансамбли, кластеризация и снижение размерности, "
            "Recsys, NLP, мониторинг качества), DL (CNN, RNN, NLP, generative models, VAE, RL, GNN, "
            "metric learning), базовый Python, алгоритмы и структуры данных.")
for line in textwrap.wrap(edu_text, width=100):
    c.drawString(left, y, line)
    y -= 14
y -= 8

section("Технические навыки")
for t in [
    "Языки: Python, Go, SQL",
    "ML: PyTorch, TensorFlow, scikit-learn, Pandas, NumPy, OpenCV",
    "Retrieval / Embeddings: FAISS, vector search",
    "Инженерные инструменты: Docker, FastAPI, gRPC, Git, Linux"
]:
    bullet_line(t)
y -= 6

section("Проекты")
c.setFont("DejaVuSans-Bold", 11)
c.drawString(left, y, "Neural Networks implementations")
y -= 14
c.setFont("DejaVuSans", 11)
c.drawString(left, y, "GitHub: https://github.com/HoLuG/NeuralNetworks")
y -= 16

for t in [
    "Реализация и эксперименты с моделями ML и нейронными сетями в рамках учебных заданий.",
    "Обучение и оценка моделей, работа с датасетами, анализ метрик качества, подбор параметров."
]:
    bullet_line(t)
y -= 6

section("Интересы")
interests = "Machine Learning • Deep Learning • Computer Vision • NLP • Retrieval-системы • RAG-архитектуры • ML-сервисы и инфраструктура"
for line in textwrap.wrap(interests, width=105):
    c.drawString(left, y, line)
    y -= 14
y -= 8

section("Роль на хакатоне")
role = "ML Engineer: построение моделей, embeddings/retrieval, мультимодальные пайплайны и интеграция ML-компонентов в сервис."
for line in textwrap.wrap(role, width=105):
    c.drawString(left, y, line)
    y -= 14

c.showPage()
c.save()

pdf_path
