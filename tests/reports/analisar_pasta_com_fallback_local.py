from __future__ import annotations

import argparse
import asyncio
import json
from pathlib import Path

import main


def _ler_arquivos_da_pasta(pasta: Path) -> list[tuple[str, bytes]]:
    arquivos = []
    for p in sorted(pasta.iterdir(), key=lambda x: x.name.lower()):
        if not p.is_file():
            continue
        if p.name.lower() == "fixture.json":
            continue
        arquivos.append((p.name, p.read_bytes()))
    return arquivos


async def _run(pasta: Path, modo: str) -> dict:
    arquivos = _ler_arquivos_da_pasta(pasta)
    texto, meta = main.montar_texto_caso_classificado_raw(arquivos)
    ficha = await main.analisar_com_fallback(texto, num_docs=len(arquivos), modo=modo)
    return {"pasta": str(pasta), "modo": modo, "meta": meta, "ficha": ficha}


def main_cli() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--pasta", required=True)
    ap.add_argument("--modo", default="auto", choices=["auto", "parser", "ia"])
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    pasta = Path(args.pasta)
    if not pasta.exists():
        raise SystemExit(f"Pasta não encontrada: {pasta}")

    data = asyncio.run(_run(pasta, args.modo))
    Path(args.out).write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main_cli())

