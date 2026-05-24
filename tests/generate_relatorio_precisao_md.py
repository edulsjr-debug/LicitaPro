#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path


PESOS_DEFAULT = {
    "numero_edital": 12,
    "orgao": 12,
    "cnpj": 8,
    "modalidade": 10,
    "objeto": 18,
    "valor": 12,
    "data_abertura": 12,
    "prazo_vigencia": 6,
    "criterio_julgamento": 6,
    "documentos_habilitacao": 4,
}


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _md_cell(x) -> str:
    if x is None:
        return ""
    s = str(x)
    s = s.replace("\n", " ").replace("|", "\\|")
    return s


def _infer_ok_from_check(chk: dict) -> bool:
    return bool(chk.get("ok"))


def _peso_perdido_por_campo(report: dict) -> dict[str, int]:
    perdidos: dict[str, int] = {}
    for caso in report.get("casos", []):
        for chk in caso.get("checks", []):
            if chk.get("tipo") != "esperado":
                continue
            campo = chk.get("campo") or ""
            perdidos[campo] = perdidos.get(campo, 0) + int(chk.get("peso_perdido") or 0)
    return perdidos


def _render(report: dict) -> str:
    editais_dir = report.get("editais_dir", "")
    pesos = report.get("pesos_confianca") or PESOS_DEFAULT
    casos = report.get("casos", [])

    gen_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    linhas: list[str] = []
    linhas.append("# Relatorio de Precisao do Parser")
    linhas.append("")
    linhas.append("Base da medicao:")
    linhas.append("")
    linhas.append(f"- Gerado em: `{gen_at}`")
    if editais_dir:
        linhas.append(f"- Diretorio dos editais: `{editais_dir}`")
    linhas.append("- Execucao: `python tests/run_fixtures.py`")
    linhas.append("- Fallback de IA: desabilitado na medicao (parser puro)")
    linhas.append("")
    linhas.append("## Resumo")
    linhas.append("")
    linhas.append("| Caso | Confianca final | Score final | Peso total avaliado | Peso perdido |")
    linhas.append("|---|---:|---:|---:|---:|")
    for caso in casos:
        linhas.append(
            f"| `{_md_cell(caso.get('id'))}` | "
            f"{_md_cell(caso.get('confianca_final'))}% | "
            f"{_md_cell(caso.get('score_final'))} | "
            f"{_md_cell(caso.get('peso_total'))} | "
            f"{_md_cell(caso.get('peso_perdido'))} |"
        )
    linhas.append("")
    total_ok = int(report.get("total_ok") or 0)
    total_falha = int(report.get("total_falha") or 0)
    linhas.append(f"Resultado global: `{total_ok}/{total_ok + total_falha}` verificacoes OK.")
    linhas.append("")
    linhas.append("## Detalhamento por caso")
    linhas.append("")

    for caso in casos:
        cid = caso.get("id")
        linhas.append(f"### `{_md_cell(cid)}`")
        linhas.append("")
        linhas.append(f"Confianca final: **{_md_cell(caso.get('confianca_final'))}%**")
        linhas.append("")
        linhas.append("| Campo | Peso | Extraido | Esperado | Acertou |")
        linhas.append("|---|---:|---|---|---|")
        checks = [c for c in (caso.get("checks") or []) if c.get("tipo") == "esperado"]
        if not checks:
            linhas.append(f"| (sem gabarito) | 0 |  |  |  |")
            linhas.append("")
            continue

        for chk in checks:
            campo = chk.get("campo") or ""
            peso = int(chk.get("peso") or pesos.get(campo, 0) or 0)
            extraido = chk.get("valor_real")
            esperado = chk.get("regra")
            ok = "S" if _infer_ok_from_check(chk) else "N"
            linhas.append(
                f"| {campo} | {peso} | "
                f"`{_md_cell(extraido)}` | "
                f"`{_md_cell(esperado)}` | {ok} |"
            )
        linhas.append("")

    linhas.append("## Ranking dos campos que mais falham")
    linhas.append("")
    linhas.append("Criterio: soma dos pesos perdidos entre todos os casos que possuem gabarito.")
    linhas.append("")
    perdidos = _peso_perdido_por_campo(report)
    linhas.append("| Campo | Peso perdido total |")
    linhas.append("|---|---:|")
    for campo, peso in sorted(perdidos.items(), key=lambda kv: (-kv[1], kv[0])):
        linhas.append(f"| {campo} | {peso} |")
    if not perdidos:
        linhas.append("| (nenhum) | 0 |")
    linhas.append("")

    return "\n".join(linhas)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="inp", default="tests/relatorio_por_pasta.json")
    ap.add_argument("--out", dest="out", default="tests/relatorio_precisao.md")
    args = ap.parse_args()

    data = _load(Path(args.inp))
    md = _render(data)
    Path(args.out).write_text(md, encoding="utf-8")
    print(f"OK: wrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

