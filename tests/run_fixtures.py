#!/usr/bin/env python3
"""
Verifica o parser contra o gabarito de PDFs de referência.

Uso:
  python tests/run_fixtures.py
  EDITAIS_DIR=/outro/caminho python tests/run_fixtures.py
  python tests/run_fixtures.py --id poco_verde   # roda só um fixture

Retorna exit code 0 se tudo OK, 1 se alguma verificação falhou.
"""
import argparse
import io
import json
import os
import sys
from pathlib import Path

# garante que importa o parser do repo, não de um pacote instalado
ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

try:
    import pdfplumber
except ImportError:
    print("ERRO: pdfplumber não instalado. Execute: pip install pdfplumber")
    sys.exit(2)

from parser_edital import analisar_sem_api

FIXTURES_PATH = ROOT / "tests" / "fixtures.json"


def _check(nome: str, valor_real, regra) -> tuple[bool, str]:
    real_str = str(valor_real or "")

    if isinstance(regra, str):
        ok = real_str == regra
        return ok, f"'{real_str}' == '{regra}'"

    if isinstance(regra, dict):
        if "contem" in regra:
            termos = regra["contem"]
            ok = all(t.upper() in real_str.upper() for t in termos)
            return ok, f"'{real_str}' contem {termos}"
        if "min" in regra or "max" in regra:
            try:
                num = float(real_str.replace(".", "").replace(",", "."))
            except ValueError:
                return False, f"'{real_str}' não é numérico"
            mn, mx = regra.get("min"), regra.get("max")
            if mn is not None and num < mn:
                return False, f"{num} < mínimo {mn}"
            if mx is not None and num > mx:
                return False, f"{num} > máximo {mx}"
            return True, f"{num} em [{mn}, {mx}]"

    return False, f"regra desconhecida: {regra!r}"


def _check_nao(nome: str, valor_real, proibidos: list) -> tuple[bool, str]:
    real_upper = str(valor_real or "").upper()
    for p in proibidos:
        if p.upper() in real_upper:
            return False, f"'{valor_real}' contém valor proibido '{p}'"
    return True, f"'{valor_real}' não contém {proibidos}"


def rodar_fixture(fx: dict, editais_dir: Path) -> tuple[int, int]:
    """Retorna (ok, falha) para o fixture."""
    ok_total = 0
    falha_total = 0

    pdf_path = editais_dir / fx["arquivo"]
    if not pdf_path.exists():
        print(f"  SKIP — arquivo não encontrado: {pdf_path}")
        return 0, 0

    tamanho = pdf_path.stat().st_size
    tamanho_esperado = fx.get("tamanho_bytes")
    if tamanho_esperado and tamanho != tamanho_esperado:
        print(f"  AVISO — tamanho diferente: {tamanho} bytes (gabarito: {tamanho_esperado})")

    try:
        with open(pdf_path, "rb") as f:
            data = f.read()
        max_pgs = fx.get("max_paginas")
        with pdfplumber.open(io.BytesIO(data)) as pdf:
            paginas = pdf.pages[:max_pgs] if max_pgs else pdf.pages
            texto = "\n".join(p.extract_text() or "" for p in paginas)
        resultado = analisar_sem_api(texto)
    except Exception as e:
        print(f"  ERRO ao processar PDF: {e}")
        return 0, 1

    for campo, regra in fx.get("esperado", {}).items():
        valor = resultado.get(campo, "N/A")
        ok, msg = _check(campo, valor, regra)
        if ok:
            print(f"  OK {campo}: {msg}")
            ok_total += 1
        else:
            print(f"  XX {campo}: FALHOU — {msg}")
            falha_total += 1

    for campo, proibidos in fx.get("nao_esperado", {}).items():
        valor = resultado.get(campo, "")
        ok, msg = _check_nao(campo, valor, proibidos)
        if ok:
            print(f"  OK {campo} (não esperado): {msg}")
            ok_total += 1
        else:
            print(f"  XX {campo} (não esperado): FALHOU — {msg}")
            falha_total += 1

    return ok_total, falha_total


def main():
    parser = argparse.ArgumentParser(description="Verifica parser contra gabarito de PDFs")
    parser.add_argument("--id", help="Roda só o fixture com esse id")
    args = parser.parse_args()

    dados = json.loads(FIXTURES_PATH.read_text(encoding="utf-8"))
    editais_dir_env = os.getenv("EDITAIS_DIR", dados.get("editais_dir", ""))
    editais_dir = Path(editais_dir_env)

    print(f"Gabarito: {dados['versao']}")
    print(f"Editais dir: {editais_dir}")

    fixtures = dados["fixtures"]
    if args.id:
        fixtures = [f for f in fixtures if f["id"] == args.id]
        if not fixtures:
            print(f"ERRO: fixture '{args.id}' não encontrado")
            sys.exit(2)

    total_ok = 0
    total_falha = 0

    for fx in fixtures:
        print(f"\n{'='*60}")
        print(f"[{fx['id']}] {fx['descricao']}")
        if fx.get("nota"):
            print(f"  Nota: {fx['nota']}")
        ok, falha = rodar_fixture(fx, editais_dir)
        total_ok += ok
        total_falha += falha

    print(f"\n{'='*60}")
    print(f"Resultado: {total_ok}/{total_ok + total_falha} verificações OK")
    if total_falha:
        print(f"FALHOU: {total_falha} verificações")
        sys.exit(1)
    else:
        print("TUDO OK — nenhuma regressão detectada")
        sys.exit(0)


if __name__ == "__main__":
    main()
