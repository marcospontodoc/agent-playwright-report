"""Gráficos vetoriais compactos para inclusão direta no PDF."""

from __future__ import annotations

from reportlab.graphics.shapes import Drawing, Rect, String
from reportlab.graphics.charts.piecharts import Pie
from reportlab.lib import colors


COLORS = {
    "expected": "#238636", "unexpected": "#cf222e", "flaky": "#bf8700",
    "skipped": "#6e7781", "unknown": "#8250df",
}


def pie_chart(approved: int, failed: int, width: int = 330, height: int = 150) -> Drawing:
    """Circular distribution using only deterministically extracted pass/fail counts."""
    drawing = Drawing(width, height)
    pie = Pie()
    pie.x, pie.y, pie.width, pie.height = 18, 8, 125, 125
    pie.data = [approved, failed]
    pie.labels = ["", ""]
    pie.slices[0].fillColor = colors.HexColor(COLORS["expected"])
    pie.slices[1].fillColor = colors.HexColor(COLORS["unexpected"])
    if approved == 0 and failed == 0:
        return drawing
    drawing.add(pie)
    drawing.add(String(165, 93, f"Aprovados: {approved}", fontName="Helvetica-Bold", fontSize=10,
                       fillColor=COLORS["expected"]))
    drawing.add(String(165, 70, f"Falhos: {failed}", fontName="Helvetica-Bold", fontSize=10,
                       fillColor=COLORS["unexpected"]))
    return drawing


def bar_chart(title: str, rows: list[tuple[str, int]], width: int = 500, row_height: int = 25) -> Drawing:
    height = 36 + max(1, len(rows)) * row_height
    drawing = Drawing(width, height)
    drawing.add(String(0, height - 15, title, fontName="Helvetica-Bold", fontSize=10, fillColor="#24292f"))
    max_value = max((value for _, value in rows), default=0) or 1
    label_width = min(180, max(100, width * 0.38))
    bar_width = width - label_width - 55
    for index, (label, value) in enumerate(rows):
        y = height - 37 - (index + 1) * row_height
        drawing.add(String(0, y + 4, label[:32], fontName="Helvetica", fontSize=8, fillColor="#57606a"))
        w = max(1, bar_width * value / max_value) if value else 0
        drawing.add(Rect(label_width, y, w, 13, fillColor="#0969da", strokeColor=None))
        drawing.add(String(label_width + w + 5, y + 3, str(value), fontName="Helvetica-Bold", fontSize=8, fillColor="#24292f"))
    return drawing


def status_chart(rows: list[tuple[str, int]], width: int = 500, height: int = 88) -> Drawing:
    drawing = Drawing(width, height)
    drawing.add(String(0, height - 15, "Distribuição geral por status", fontName="Helvetica-Bold", fontSize=10, fillColor="#24292f"))
    total = sum(v for _, v in rows)
    x = 0
    bar_y = 38
    bar_h = 22
    usable = width
    for status, value in rows:
        if value == 0 or total == 0:
            continue
        segment = usable * value / total
        drawing.add(Rect(x, bar_y, segment, bar_h, fillColor=COLORS.get(status, COLORS["unknown"]), strokeColor=None))
        x += segment
    x = 0
    for status, value in rows:
        if value == 0:
            continue
        label = f"{status}: {value}"
        drawing.add(String(x, 17, label, fontName="Helvetica", fontSize=7.5, fillColor=COLORS.get(status, COLORS["unknown"])))
        x += max(82, len(label) * 4.5)
    if total == 0:
        drawing.add(String(0, bar_y + 6, "Sem resultados para representar", fontName="Helvetica-Oblique", fontSize=8, fillColor="#57606a"))
    return drawing

