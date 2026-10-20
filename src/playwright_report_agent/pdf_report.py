"""Geração do relatório conciso conforme o modelo único do projeto."""

from __future__ import annotations

import re
from datetime import datetime, timezone
from html import escape
from pathlib import Path
from typing import Any

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import BaseDocTemplate, Frame, PageTemplate, Paragraph, Spacer, Image

from .charts import pie_chart
from .metrics import Metrics


def read_document(path: Path) -> str:
    """Read supported functional documentation without executing embedded content."""
    suffix = path.suffix.lower()
    try:
        if suffix in {".md", ".txt"}:
            text = path.read_text(encoding="utf-8")
        elif suffix == ".pdf":
            from pypdf import PdfReader
            text = "\n".join(page.extract_text() or "" for page in PdfReader(str(path)).pages)
        elif suffix == ".docx":
            from docx import Document
            text = "\n".join(p.text for p in Document(str(path)).paragraphs)
        else:
            raise ValueError(f"Formato de documentação não suportado: {suffix or '(sem extensão)'}.")
    except Exception as exc:
        if isinstance(exc, ValueError):
            raise
        raise ValueError(f"Não foi possível ler a documentação {path}: {exc}") from exc
    if not text.strip():
        raise ValueError(f"A documentação não contém texto legível: {path}")
    return text


def _styles():
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="TitlePT", parent=styles["Title"], fontName="Helvetica-Bold", fontSize=19,
                              leading=23, textColor=colors.HexColor("#17365d"), alignment=TA_CENTER, spaceAfter=4))
    styles.add(ParagraphStyle(name="SubPT", parent=styles["Normal"], fontSize=8, leading=11,
                              textColor=colors.HexColor("#57606a"), alignment=TA_CENTER, spaceAfter=12))
    styles.add(ParagraphStyle(name="SectionPT", parent=styles["Heading1"], fontSize=13, leading=16,
                              textColor=colors.HexColor("#17365d"), spaceBefore=8, spaceAfter=5, keepWithNext=True))
    styles.add(ParagraphStyle(name="BodyPT", parent=styles["BodyText"], fontSize=9, leading=12, spaceAfter=5))
    styles.add(ParagraphStyle(name="SmallPT", parent=styles["BodyText"], fontSize=8, leading=10, textColor=colors.HexColor("#57606a")))
    return styles


class _ReportDoc(BaseDocTemplate):
    def __init__(self, filename: Path):
        super().__init__(str(filename), pagesize=A4, title="Relatório de Testes", author="Agente de Relatórios Playwright")
        frame = Frame(18 * mm, 17 * mm, A4[0] - 36 * mm, A4[1] - 34 * mm, id="normal")
        self.addPageTemplates(PageTemplate(id="main", frames=frame, onPage=self._footer))

    @staticmethod
    def _footer(canvas, doc):
        canvas.saveState()
        canvas.setStrokeColor(colors.HexColor("#d0d7de"))
        canvas.line(18 * mm, 13 * mm, A4[0] - 18 * mm, 13 * mm)
        canvas.setFont("Helvetica", 7)
        canvas.setFillColor(colors.HexColor("#57606a"))
        canvas.drawRightString(A4[0] - 18 * mm, 8.5 * mm, f"Página {doc.page}")
        canvas.restoreState()


def create_pdf(output_path: Path, source_path: Path, report: dict[str, Any], metrics: Metrics,
               document_path: Path, execution_context: dict[str, Any], template_path: Path | None = None) -> None:
    template_path = template_path or Path("templates/modelo-relatorio.md")
    try:
        template_text = template_path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        raise ValueError(f"Não foi possível ler o modelo {template_path}: {exc}") from exc
    headings = re.findall(r"^\s*([1-4])\\?\.\s+(Objetivo|Resultado dos Testes|Bugs Encontrados|Conclusão)\s*$",
                          template_text, flags=re.M)
    required = ["Objetivo", "Resultado dos Testes", "Bugs Encontrados", "Conclusão"]
    if [name for _, name in headings] != required or [int(n) for n, _ in headings] != [1, 2, 3, 4]:
        raise ValueError("O modelo precisa conter as quatro seções obrigatórias, na ordem definida.")

    doc_text = read_document(document_path)
    lines = [line.strip() for line in doc_text.splitlines() if line.strip()]
    project = re.sub(r"^#+\s*", "", lines[0]) if lines else document_path.stem
    project = re.sub(r"^Contexto funcional do projeto\s*:\s*", "", project, flags=re.I)
    styles = _styles()
    story: list[Any] = [Paragraph("Relatório de Testes", styles["TitlePT"]),
                        Paragraph(escape(project) + " · " + escape(source_path.name), styles["SubPT"])]

    def section(index: int) -> None:
        story.append(Paragraph(f"{index}. {required[index - 1]}", styles["SectionPT"]))

    section(1)
    story.append(Paragraph(
        f"Esta execução apresenta os resultados dos testes automatizados de {escape(project)}, realizados com Playwright para verificar os comportamentos descritos na documentação funcional.",
        styles["BodyPT"]))

    section(2)
    story.append(Paragraph("Distribuição dos resultados registrados na execução:", styles["BodyPT"]))
    approved, failed = metrics.by_status["expected"], metrics.by_status["unexpected"]
    if approved + failed:
        story.append(pie_chart(approved, failed))
    else:
        story.append(Paragraph("Gráfico indisponível: não há resultados aprovados ou falhos para representar.", styles["BodyPT"]))
    denominator = approved + failed
    success = f"{100 * approved / denominator:.1f}%" if denominator else "Não calculável"
    story.append(Paragraph(
        f"Total: {metrics.total} · Aprovados: {approved} · Falhos: {failed} · Ignorados: {metrics.by_status['skipped']} · Instáveis: {metrics.by_status['flaky']}.", styles["BodyPT"]))
    story.append(Paragraph(f"Taxa de sucesso: {success}.", styles["BodyPT"]))
    if metrics.by_status["unexpected"]:
        story.append(Paragraph(f"{metrics.by_status['unexpected']} falha(s) de teste precisam ser analisadas.", styles["BodyPT"]))

    section(3)
    story.append(Paragraph("Nenhum bug confirmado nesta execução.", styles["BodyPT"]))

    section(4)
    if not metrics.total:
        conclusion = "O HTML não registrou resultados individuais suficientes para avaliar a execução."
    elif failed:
        conclusion = f"Foram executados {metrics.total} testes automatizados, com {approved} aprovados, {failed} falhos e taxa de sucesso de {success}. As falhas registradas precisam ser analisadas."
    elif approved == metrics.total:
        conclusion = f"Foram executados {metrics.total} testes automatizados, todos aprovados, com taxa de sucesso de {success}. A execução foi concluída sem falhas registradas."
    else:
        conclusion = f"Foram executados {metrics.total} testes automatizados, com {approved} aprovados e taxa de sucesso de {success}. A execução foi concluída sem falhas registradas."
    story.append(Paragraph(escape(conclusion), styles["BodyPT"]))
    _ReportDoc(output_path).build(story)


def _run_start(report: dict[str, Any]) -> str:
    value = report.get("startTime")
    try:
        return datetime.fromtimestamp(float(value) / 1000, tz=timezone.utc).strftime("%d/%m/%Y %H:%M UTC")
    except (TypeError, ValueError, OSError):
        return "Não informado"
