from __future__ import annotations

import os
from pathlib import Path

from openpyxl import Workbook, load_workbook


def copy_sheet_values(src_ws, dst_ws):
    # Copy only cell values/formulas (no styles) to keep file robust.
    max_row = src_ws.max_row
    max_col = src_ws.max_column
    for r in range(1, max_row + 1):
        for c in range(1, max_col + 1):
            v = src_ws.cell(r, c).value
            if v is not None and v != "":
                dst_ws.cell(r, c).value = v

    # Copy column widths if present (optional, cosmetic)
    for col, dim in src_ws.column_dimensions.items():
        if dim.width:
            dst_ws.column_dimensions[col].width = dim.width


def build_kendall_sheet(ws1, ws2):
    # Headers
    ws2["A1"] = ws1["A1"].value or "X"
    ws2["B1"] = ws1["B1"].value or "Y"
    ws2["C1"] = "R_i (# справа больше Y)"
    ws2["D1"] = "R_i (формула)"

    # Read data, sort by X then Y (textbook method)
    raw = []
    for r in range(2, 19):
        xv = ws1[f"A{r}"].value
        yv = ws1[f"B{r}"].value
        if xv is None or yv is None:
            continue
        raw.append((float(xv), float(yv)))
    raw.sort(key=lambda t: (t[0], t[1]))

    n = len(raw)
    last_row = 1 + n
    for i, (xv, yv) in enumerate(raw, start=2):
        ws2[f"A{i}"] = xv
        ws2[f"B{i}"] = yv

    for r in range(2, last_row + 1):
        if r == last_row:
            ws2[f"C{r}"] = 0
            ws2[f"D{r}"] = "последняя строка"
        else:
            # Russian locale separator ';'
            ws2[f"D{r}"] = f'=COUNTIF($B{r+1}:$B${last_row};\">\"&B{r})'
            ws2[f"C{r}"] = f"={ws2[f'D{r}'].coordinate}"

    # Summary (use RU function names to match RU Excel locale)
    ws2["I1"] = "Критерий Кендалла (tau)"
    ws2["I3"] = "n="
    ws2["J3"] = n
    ws2["I4"] = "N0=n(n-1)/2"
    ws2["J4"] = "=J3*(J3-1)/2"
    ws2["I5"] = "R=Σ R_i"
    ws2["J5"] = f"=SUM(C2:C{last_row})"
    ws2["I6"] = "tau (по R)"
    ws2["J6"] = "=4*J5/(J3*(J3-1)) - 1"
    ws2["I8"] = "z (H0: tau=0)"
    ws2["J8"] = "=J6*SQRT(9*J3*(J3-1)/(2*(2*J3+5)))"
    ws2["I9"] = "p-value (двуст.)"
    # Prefer Russian function names; fallback to English via ЕСЛИОШИБКА.
    ws2["J9"] = "=ЕСЛИОШИБКА(2*(1-НОРМ.СТ.РАСП(ABS(J8);ИСТИНА));2*(1-NORM.S.DIST(ABS(J8);TRUE)))"
    ws2["I14"] = "α"
    ws2["J14"] = 0.05
    ws2["I15"] = "Решение"
    ws2["J15"] = '=ЕСЛИ(J9<J14;"отвергаем H0 (связь есть)";"нет оснований отвергнуть H0")'

    # Column widths
    for col, w in [("A", 10), ("B", 10), ("C", 20), ("D", 22), ("I", 26), ("J", 24)]:
        ws2.column_dimensions[col].width = w


def main() -> None:
    base = Path(__file__).resolve().parents[1]
    new_task = base / "new_task"
    xlsx_files = sorted([new_task / f for f in os.listdir(new_task) if f.lower().endswith(".xlsx")])
    if not xlsx_files:
        raise SystemExit("No xlsx files found in new_task/.")

    # pick workbook that starts with Домрачева if possible, else first
    target = None
    for f in xlsx_files:
        if "Домрачева" in f.name or "РК" in f.name:
            target = f
            break
    if target is None:
        target = xlsx_files[0]

    src = load_workbook(target, data_only=True)
    ws_src = src[src.sheetnames[0]]

    # Build a new, minimal workbook to avoid Excel "repair"
    wb = Workbook()
    wsA = wb.active
    wsA.title = "Лист1"
    wsB = wb.create_sheet(title="Лист2", index=1)
    wb.create_sheet(title="Лист3", index=2)

    # Copy only the first table (A1:F1, A2:B18) as values (no formulas like _xlfn.*)
    wsA["A1"] = ws_src["A1"].value or "Рост в см"
    wsA["B1"] = ws_src["B1"].value or "Вес в кг"
    for r in range(2, 19):
        wsA[f"A{r}"] = ws_src[f"A{r}"].value
        wsA[f"B{r}"] = ws_src[f"B{r}"].value

    wsA.column_dimensions["A"].width = 10
    wsA.column_dimensions["B"].width = 10

    build_kendall_sheet(wsA, wsB)

    wb.save(target)
    print("Rebuilt (minimal, Excel-safe) workbook:", target)


if __name__ == "__main__":
    main()

