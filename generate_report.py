"""Executável simples para gerar relatórios Playwright em PDF."""

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from playwright_report_agent.cli import main


if __name__ == "__main__":
    raise SystemExit(main())
