"""Extração segura dos dados JSON embutidos no HTML do Playwright."""

from __future__ import annotations

import base64
import binascii
import io
import json
import re
import zipfile
from dataclasses import dataclass
from html.parser import HTMLParser
from pathlib import Path
from typing import Any


MAX_HTML_BYTES = 100 * 1024 * 1024
MAX_JSON_BYTES = 50 * 1024 * 1024
MAX_ARCHIVE_ENTRIES = 10_000
MAX_ARCHIVE_UNCOMPRESSED_BYTES = 500 * 1024 * 1024


class ReportExtractionError(ValueError):
    """O relatório não pode ser interpretado com segurança ou está incompleto."""


class _TemplateReader(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.templates: list[str] = []
        self._inside = False
        self._parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() == "template" and dict(attrs).get("id") == "playwrightReportBase64":
            if self._inside:
                raise ReportExtractionError("Template ZIP duplicado no HTML.")
            self._inside = True
            self._parts = []

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() == "template" and self._inside:
            self.templates.append("".join(self._parts))
            self._inside = False
            self._parts = []

    def handle_data(self, data: str) -> None:
        if self._inside:
            self._parts.append(data)


@dataclass
class ExtractedReport:
    report: dict[str, Any]
    details_by_test_id: dict[str, dict[str, Any]]


def extract_report(html_path: Path) -> ExtractedReport:
    try:
        size = html_path.stat().st_size
    except OSError as exc:
        raise ReportExtractionError(f"Não foi possível acessar o HTML: {exc}") from exc
    if size == 0 or size > MAX_HTML_BYTES:
        raise ReportExtractionError("Tamanho do HTML vazio ou acima do limite de segurança (100 MiB).")

    try:
        html = html_path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        raise ReportExtractionError(f"Não foi possível ler o HTML como UTF-8: {exc}") from exc

    reader = _TemplateReader()
    try:
        reader.feed(html)
        reader.close()
    except ReportExtractionError:
        raise
    except Exception as exc:
        raise ReportExtractionError(f"HTML malformado: {exc}") from exc
    if len(reader.templates) != 1:
        raise ReportExtractionError("Era esperado exatamente um template playwrightReportBase64.")

    match = re.fullmatch(r"\s*data:application/zip;base64,([A-Za-z0-9+/=\s]+)\s*", reader.templates[0])
    if not match:
        raise ReportExtractionError("O template não contém um ZIP Base64 no formato esperado.")
    try:
        archive_bytes = base64.b64decode(re.sub(r"\s+", "", match.group(1)), validate=True)
    except (binascii.Error, ValueError) as exc:
        raise ReportExtractionError("O conteúdo Base64 do relatório é inválido.") from exc

    try:
        with zipfile.ZipFile(io.BytesIO(archive_bytes)) as archive:
            infos = archive.infolist()
            if len(infos) > MAX_ARCHIVE_ENTRIES:
                raise ReportExtractionError("O ZIP excede o limite de entradas permitido.")
            if sum(item.file_size for item in infos) > MAX_ARCHIVE_UNCOMPRESSED_BYTES:
                raise ReportExtractionError("O conteúdo descompactado do ZIP excede 500 MiB.")
            names = [item.filename for item in infos]
            if len(set(names)) != len(names):
                raise ReportExtractionError("O ZIP contém nomes de arquivo duplicados.")
            report_names = [item for item in infos if item.filename == "report.json"]
            if len(report_names) != 1:
                raise ReportExtractionError("O ZIP deve conter exatamente um report.json.")

            report = _read_json_member(archive, report_names[0])
            if not isinstance(report, dict) or not isinstance(report.get("files"), list):
                raise ReportExtractionError("report.json não contém a estrutura files esperada.")
            details: dict[str, dict[str, Any]] = {}
            for info in infos:
                if info.filename == "report.json" or not info.filename.lower().endswith(".json"):
                    continue
                if info.file_size > MAX_JSON_BYTES:
                    raise ReportExtractionError(f"Arquivo JSON interno acima do limite: {info.filename}")
                obj = _read_json_member(archive, info)
                if isinstance(obj, dict) and isinstance(obj.get("tests"), list):
                    for test in obj["tests"]:
                        if isinstance(test, dict) and isinstance(test.get("testId"), str):
                            details[test["testId"]] = test
            _validate_report_shape(report)
            return ExtractedReport(report=report, details_by_test_id=details)
    except ReportExtractionError:
        raise
    except (OSError, zipfile.BadZipFile, RuntimeError, json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise ReportExtractionError(f"O ZIP/JSON interno do relatório está inválido: {exc}") from exc


def _read_json_member(archive: zipfile.ZipFile, info: zipfile.ZipInfo) -> Any:
    if info.file_size > MAX_JSON_BYTES:
        raise ReportExtractionError(f"Arquivo JSON interno acima do limite: {info.filename}")
    try:
        return json.loads(archive.read(info))
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise ReportExtractionError(f"JSON inválido no arquivo interno {info.filename}.") from exc


def _validate_report_shape(report: dict[str, Any]) -> None:
    if not isinstance(report.get("stats"), dict):
        raise ReportExtractionError("report.json não contém estatísticas gerais.")
    for file_data in report["files"]:
        if not isinstance(file_data, dict) or not isinstance(file_data.get("tests"), list):
            raise ReportExtractionError("Há um arquivo sem a lista tests esperada.")
        for test in file_data["tests"]:
            if not isinstance(test, dict):
                raise ReportExtractionError("Há um resultado de teste em formato inválido.")

