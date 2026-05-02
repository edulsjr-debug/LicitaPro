#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path


HERE = Path(__file__).parent
ROOT = HERE.parent.parent


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, data: dict):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2, default=str), encoding="utf-8")


def _split_report(report_path: Path) -> list[Path]:
    report = _load(report_path)
    casos = report.get("casos") or []
    if not casos:
        raise SystemExit(f"Relatorio sem casos: {report_path}")

    out_paths: list[Path] = []
    for caso in casos:
        cid = (caso.get("id") or "caso").strip()
        cid_safe = "".join(ch if ch.isalnum() or ch in ("-", "_") else "_" for ch in cid)[:80] or "caso"
        out = HERE / f"{cid_safe}.json"
        single = dict(report)
        single["total_ok"] = sum(1 for c in (caso.get("checks") or []) if c.get("ok") is True)
        single["total_falha"] = sum(1 for c in (caso.get("checks") or []) if c.get("ok") is False)
        single["casos"] = [caso]
        _write_json(out, single)
        out_paths.append(out)
    return out_paths


def _html_to_pdf(html_path: Path, pdf_path: Path):
    import fitz  # PyMuPDF

    html_bytes = html_path.read_bytes()
    doc = fitz.open(stream=html_bytes, filetype="html")
    pdf_bytes = doc.convert_to_pdf()
    pdf = fitz.open(stream=pdf_bytes, filetype="pdf")
    pdf.save(pdf_path)


def main() -> int:
    report_path = ROOT / "tests" / "relatorio_por_pasta.json"
    if not report_path.exists():
        raise SystemExit(f"Nao achei {report_path}. Rode: python tests/run_fixtures.py --report {report_path}")

    # 1) split JSON por caso
    _split_report(report_path)

    # 2) gerar HTML por caso
    import subprocess

    subprocess.check_call(["python", str(HERE / "generate_case_reports.py")], cwd=str(HERE))

    # 3) converter HTML -> PDF
    pdf_dir = HERE / "pdf"
    pdf_dir.mkdir(parents=True, exist_ok=True)
    for html_path in sorted(HERE.glob("*.html")):
        pdf_path = pdf_dir / (html_path.stem + ".pdf")
        _html_to_pdf(html_path, pdf_path)

    print(f"OK: PDFs em {pdf_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

