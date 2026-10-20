"""Métricas determinísticas e validação de consistência dos resultados."""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
from typing import Any


STATUS_LABELS = {
    "expected": "Esperado",
    "unexpected": "Falhou / inesperado",
    "flaky": "Instável (flaky)",
    "skipped": "Ignorado",
}


class MetricsValidationError(ValueError):
    """Os totais extraídos não concordam com os resumos do Playwright."""


@dataclass
class Metrics:
    tests: list[dict[str, Any]]
    by_status: Counter[str]
    by_project: dict[str, Counter[str]]
    by_file: dict[str, Counter[str]]
    total: int
    unique_scenarios: int
    scenarios_missing_identity: int
    attempts: int
    retries: int
    expected_percent: float | None
    warnings: list[str]


def calculate_metrics(report: dict[str, Any], details_by_test_id: dict[str, dict[str, Any]]) -> Metrics:
    tests: list[dict[str, Any]] = []
    by_status: Counter[str] = Counter()
    by_project: dict[str, Counter[str]] = defaultdict(Counter)
    by_file: dict[str, Counter[str]] = defaultdict(Counter)
    identities: set[tuple[Any, ...]] = set()
    missing_identity = 0
    attempts = 0
    retries = 0

    for file_data in report["files"]:
        file_name = str(file_data.get("fileName") or "Não informado")
        for raw_test in file_data["tests"]:
            test = dict(raw_test)
            test["fileName"] = file_name
            outcome = test.get("outcome")
            status = outcome if isinstance(outcome, str) and outcome else "unknown"
            test["status"] = status
            test["details"] = details_by_test_id.get(str(test.get("testId", "")), {})
            tests.append(test)
            by_status[status] += 1
            project = str(test.get("projectName") or "Não informado")
            by_project[project][status] += 1
            by_file[file_name][status] += 1

            location = test.get("location") or {}
            title = test.get("title")
            if title and location.get("line") is not None:
                identities.add((file_name, tuple(test.get("path") or []), title,
                                location.get("line"), location.get("column")))
            else:
                missing_identity += 1

            detail_results = test["details"].get("results") or []
            root_results = test.get("results") or []
            result_entries = detail_results if detail_results else root_results
            # Testes ignorados/sem execução podem não ter qualquer entrada em results.
            attempts += len(result_entries)
            retries += sum(1 for result in result_entries
                           if isinstance(result, dict) and int(result.get("retry", 0) or 0) > 0)

    total = len(tests)
    stats = report["stats"]
    if stats.get("total") is not None and int(stats["total"]) != total:
        raise MetricsValidationError(
            f"O total geral do report.json ({stats['total']}) diverge dos resultados extraídos ({total})."
        )
    for status in ("expected", "unexpected", "flaky", "skipped"):
        if stats.get(status) is not None and int(stats[status]) != by_status[status]:
            raise MetricsValidationError(
                f"O resumo geral para {status} ({stats[status]}) diverge da contagem extraída ({by_status[status]})."
            )
    for file_data in report["files"]:
        file_stats = file_data.get("stats") or {}
        file_name = str(file_data.get("fileName") or "Não informado")
        if file_stats.get("total") is not None and int(file_stats["total"]) != len(file_data["tests"]):
            raise MetricsValidationError(f"Total inconsistente no resumo de {file_name}.")
        for status in ("expected", "unexpected", "flaky", "skipped"):
            if file_stats.get(status) is not None and int(file_stats[status]) != by_file[file_name][status]:
                raise MetricsValidationError(f"Contagem {status} inconsistente no resumo de {file_name}.")

    expected_percent = (100 * by_status["expected"] / total) if total else None
    warnings: list[str] = []
    unknown = total - sum(by_status[k] for k in ("expected", "unexpected", "flaky", "skipped"))
    if unknown:
        warnings.append(f"{unknown} resultado(s) têm estado ausente ou não reconhecido pelo extrator.")
    if missing_identity:
        warnings.append(f"{missing_identity} resultado(s) não têm dados suficientes para deduplicar cenários com segurança.")
    if any(not test["details"] for test in tests):
        warnings.append("Alguns detalhes JSON por arquivo não estavam disponíveis; mensagens de erro/anexos podem estar incompletos.")

    return Metrics(
        tests=tests, by_status=by_status, by_project=dict(by_project), by_file=dict(by_file),
        total=total, unique_scenarios=len(identities), scenarios_missing_identity=missing_identity,
        attempts=attempts, retries=retries, expected_percent=expected_percent, warnings=warnings,
    )

