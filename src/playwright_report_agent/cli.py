"""Interface de linha de comando do gerador."""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .extractor import ReportExtractionError, extract_report
from .metrics import MetricsValidationError, calculate_metrics
from .pdf_report import create_pdf


ROOT = Path(__file__).resolve().parents[2]
DOC_EXTENSIONS = {".pdf", ".docx", ".md", ".txt"}


def _one_file(directory: Path, pattern: str, description: str) -> Path:
    candidates = sorted(directory.glob(pattern)) if directory.exists() else []
    if len(candidates) != 1:
        if not candidates:
            raise ValueError(f"Nenhum arquivo {description} encontrado em {directory}.")
        raise ValueError(f"Há vários arquivos {description} em {directory}; informe um caminho explícito: " + ", ".join(p.name for p in candidates))
    return candidates[0]


def _input_document(path: Path | None) -> Path:
    if path:
        return path
    docs = ROOT / "docs"
    candidates = sorted(p for p in docs.iterdir() if p.is_file() and p.suffix.lower() in DOC_EXTENSIONS) if docs.exists() else []
    if len(candidates) != 1:
        if not candidates:
            raise ValueError(f"Nenhuma documentação funcional suportada encontrada diretamente em {docs}.")
        raise ValueError("Há várias documentações candidatas em docs; use --document para selecionar uma: " + ", ".join(p.name for p in candidates))
    return candidates[0]


def _execution_context(path: Path | None) -> dict[str, Any]:
    if path is None:
        return {}
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"Não foi possível ler o contexto da execução em JSON: {exc}") from exc
    if not isinstance(value, dict):
        raise ValueError("O contexto da execução deve ser um objeto JSON.")
    return value


def _default_output(source: Path) -> Path:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    safe_stem = re.sub(r"[^A-Za-z0-9_-]+", "-", source.stem).strip("-") or "playwright"
    base = ROOT / "outputs" / f"relatorio-{safe_stem}-{stamp}"
    candidate = base.with_suffix(".pdf")
    index = 1
    while candidate.exists():
        candidate = base.with_name(f"{base.name}-{index}").with_suffix(".pdf")
        index += 1
    return candidate


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Gera um relatório PDF a partir do HTML autocontido do Playwright.")
    parser.add_argument("html", type=Path, nargs="?", help="Caminho do relatório HTML Playwright; por padrão busca em docs/exemplo-playwright")
    parser.add_argument("--document", type=Path, help="Documentação funcional PDF, DOCX, Markdown ou texto; por padrão seleciona a única em docs/")
    parser.add_argument("--execution-context", type=Path, help="JSON opcional com contexto específico da execução")
    parser.add_argument("--output", type=Path, help="PDF de saída (não sobrescreve arquivos existentes)")
    parser.add_argument("--validate-only", action="store_true", help="Extrai e valida os números sem gerar PDF")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        html_path = args.html or _one_file(ROOT / "docs" / "exemplo-playwright", "*.html", "relatório HTML Playwright")
        document_path = _input_document(args.document)
        extracted = extract_report(html_path)
        metrics = calculate_metrics(extracted.report, extracted.details_by_test_id)
        context = _execution_context(args.execution_context)
        if args.validate_only:
            print(json.dumps({
                "source": str(html_path),
                "document": str(document_path),
                "total": metrics.total,
                "by_status": dict(metrics.by_status),
                "by_project": {k: dict(v) for k, v in metrics.by_project.items()},
                "by_file": {k: dict(v) for k, v in metrics.by_file.items()},
                "unique_scenarios": metrics.unique_scenarios,
                "attempts": metrics.attempts,
                "retries": metrics.retries,
                "duration_ms": extracted.report.get("duration"),
                "warnings": metrics.warnings,
            }, ensure_ascii=False, indent=2))
            return 0
        output = args.output or _default_output(html_path)
        if output.exists():
            raise FileExistsError(f"O arquivo de saída já existe; nada foi sobrescrito: {output}")
        output.parent.mkdir(parents=True, exist_ok=True)
        # Cria exclusivamente para impedir sobrescrita e evitar corrida entre verificação e gravação.
        with output.open("xb"):
            pass
        try:
            create_pdf(output, html_path, extracted.report, metrics, document_path, context,
                       ROOT / "templates" / "modelo-relatorio.md")
        except Exception:
            output.unlink(missing_ok=True)
            raise
        print(f"PDF gerado: {output}")
        return 0
    except (ReportExtractionError, MetricsValidationError, ValueError, FileExistsError, OSError) as exc:
        print(f"Geração interrompida: {exc}", file=sys.stderr)
        return 2

