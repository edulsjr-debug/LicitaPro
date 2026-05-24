#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import mimetypes
import re
import sys
import urllib.request
import urllib.error
from dataclasses import dataclass
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
import run_fixtures as rf  # noqa: E402


@dataclass
class RenderResult:
    base_url: str
    case_id: str
    ok: int
    fail: int
    peso_total: int
    peso_perdido: int
    extraido: dict
    checks: list[dict]
    error: str | None = None


def _parse_fields_from_ficha_md(ficha: str) -> dict:
    """
    Extrai campos principais do markdown gerado pelo parser (tabela + seção de confiança).
    É suficiente para checar os fixtures atuais.
    """
    ficha = ficha or ""
    out: dict[str, object] = {}

    # tabela principal
    table_map = {
        "Nº / Processo": "numero_edital",
        "N° / Processo": "numero_edital",
        "Órgão": "orgao",
        "Modalidade": "modalidade",
        "Critério de Julgamento": "criterio_julgamento",
        "Valor Estimado Total": "valor",
        "Vigência do Contrato": "prazo_vigencia",
        "Abertura das Propostas": "data_abertura",
        "Prazo para Envio de Proposta": "prazo_envio_proposta",
    }
    for line in ficha.splitlines():
        if not line.startswith("|"):
            continue
        # | **Campo** | valor |
        parts = [p.strip() for p in line.strip().strip("|").split("|")]
        if len(parts) < 2:
            continue
        k_raw, v = parts[0], parts[1]
        k = re.sub(r"^\*\*|\*\*$", "", k_raw).strip()
        if k in table_map:
            out[table_map[k]] = v.strip()

    # confiança
    m = re.search(r"##\s*Confian[çc]a[^\\n]*\\n\\*\\*(\\d{1,3})%\\*\\*", ficha, re.IGNORECASE)
    if m:
        try:
            out["confianca"] = int(m.group(1))
        except ValueError:
            pass

    return out


def _multipart_encode(files: list[tuple[str, bytes]], fields: dict[str, str]) -> tuple[bytes, str]:
    boundary = "----LicitaPROBoundary7b8e9c0d"
    chunks: list[bytes] = []
    crlf = b"\r\n"

    def add_part(headers: list[str], body: bytes):
        chunks.append(f"--{boundary}".encode("utf-8"))
        chunks.append(crlf.join(h.encode("utf-8") for h in headers))
        chunks.append(b"")
        chunks.append(body)

    for k, v in fields.items():
        add_part([f'Content-Disposition: form-data; name="{k}"'], v.encode("utf-8"))

    for fname, data in files:
        ctype, _ = mimetypes.guess_type(fname)
        if not ctype:
            ctype = "application/octet-stream"
        add_part(
            [
                f'Content-Disposition: form-data; name="arquivos"; filename="{fname}"',
                f"Content-Type: {ctype}",
            ],
            data,
        )

    chunks.append(f"--{boundary}--".encode("utf-8"))
    chunks.append(b"")
    return crlf.join(chunks), boundary


def _post_analisar_arquivo(base_url: str, files: list[tuple[str, bytes]], modo: str) -> dict:
    payload, boundary = _multipart_encode(files, {"modo": modo})
    req = urllib.request.Request(
        base_url.rstrip("/") + "/analisar/arquivo",
        data=payload,
        headers={
            "Content-Type": f"multipart/form-data; boundary={boundary}",
            "User-Agent": "LicitaPRO-compare/1.0",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=240) as resp:
            raw = resp.read()
        return json.loads(raw.decode("utf-8", errors="replace"))
    except urllib.error.HTTPError as e:
        body = ""
        try:
            body = (e.read() or b"").decode("utf-8", errors="replace")
        except Exception:
            body = ""
        msg = f"HTTP {e.code} {e.reason}"
        if body.strip():
            msg += f" :: {body.strip()[:800]}"
        raise RuntimeError(msg) from e


def _ler_arquivos_pasta(caso_dir: Path, arquivo_principal: str | None, apenas_principal: bool) -> list[tuple[str, bytes]]:
    out: list[tuple[str, bytes]] = []
    for p in sorted(caso_dir.iterdir(), key=lambda x: x.name.lower()):
        if not p.is_file():
            continue
        if p.name.lower() == "fixture.json":
            continue
        if apenas_principal and arquivo_principal and p.name != arquivo_principal:
            continue
        out.append((p.name, p.read_bytes()))
    if not out:
        raise FileNotFoundError(f"Nenhum arquivo para enviar em {caso_dir}")
    return out


def _avaliar_case(caso: dict, base_url: str, modo: str = "parser", apenas_principal: bool = False) -> RenderResult:
    caso_dir = Path(caso["caso_dir"])
    files = _ler_arquivos_pasta(caso_dir, caso.get("arquivo_principal"), apenas_principal)

    # Compat: o runner local suporta limitar páginas do PDF principal via fixture (`max_paginas`).
    # No Render, não temos esse parâmetro; então, para comparação justa, truncamos o PDF antes de enviar.
    max_pgs = caso.get("max_paginas")
    if max_pgs and isinstance(max_pgs, int) and max_pgs > 0:
        principal = caso.get("arquivo_principal")
        if principal and principal.lower().endswith(".pdf"):
            try:
                import fitz  # PyMuPDF

                for i, (fname, data) in enumerate(list(files)):
                    if fname != principal:
                        continue
                    src = fitz.open(stream=data, filetype="pdf")
                    dst = fitz.open()
                    for pno in range(min(max_pgs, src.page_count)):
                        dst.insert_pdf(src, from_page=pno, to_page=pno)
                    files[i] = (fname, dst.tobytes())
                    src.close()
                    dst.close()
            except Exception:
                # se falhar, segue com o PDF inteiro (pode falhar no Render).
                pass
    try:
        resp = _post_analisar_arquivo(base_url, files, modo=modo)
        ficha = (resp.get("ficha") or "").strip()
    except Exception as e:
        return RenderResult(
            base_url=base_url,
            case_id=caso.get("id") or "",
            ok=0,
            fail=0,
            peso_total=sum(rf.PESOS_CONFIANCA.get(c, 0) for c in (caso.get("esperado") or {}).keys()),
            peso_perdido=0,
            extraido={},
            checks=[],
            error=str(e),
        )
    extraido = _parse_fields_from_ficha_md(ficha)

    ok_total = 0
    fail_total = 0
    peso_total = 0
    peso_perdido = 0
    checks: list[dict] = []

    for campo, regra in (caso.get("esperado") or {}).items():
        peso = rf.PESOS_CONFIANCA.get(campo, 0)
        peso_total += peso
        valor = extraido.get(campo, "N/A")
        ok, msg = rf._check(valor, regra)
        perdido = rf._peso_perdido(valor, regra, peso)
        peso_perdido += perdido
        checks.append(
            {
                "campo": campo,
                "peso": peso,
                "valor_real": valor,
                "regra": regra,
                "ok": ok,
                "msg": msg,
                "peso_perdido": perdido,
            }
        )
        if ok:
            ok_total += 1
        else:
            fail_total += 1

    for campo, proibidos in (caso.get("nao_esperado") or {}).items():
        valor = extraido.get(campo, "")
        ok, msg = rf._check_nao(valor, proibidos)
        checks.append({"campo": campo, "proibidos": proibidos, "valor_real": valor, "ok": ok, "msg": msg})
        if ok:
            ok_total += 1
        else:
            fail_total += 1

    return RenderResult(
        base_url=base_url,
        case_id=caso.get("id") or "",
        ok=ok_total,
        fail=fail_total,
        peso_total=peso_total,
        peso_perdido=peso_perdido,
        extraido=extraido,
        checks=checks,
    )


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--editais-dir", default="C:/Users/lisia/Desktop/editais")
    ap.add_argument("--base-url", required=True)
    ap.add_argument("--out", default="tests/reports/render_compare.json")
    ap.add_argument("--id", action="append", help="Filtra por id do caso (pode repetir).")
    ap.add_argument("--apenas-principal", action="store_true", help="Envia apenas o arquivo_principal de cada pasta.")
    args = ap.parse_args()

    editais_dir = Path(args.editais_dir)
    casos = rf._carregar_casos(editais_dir)
    # só compara quem tem fixture (gabarito). casos "implícitos" não têm esperado.
    casos = [c for c in casos if (c.get("esperado") or c.get("nao_esperado"))]
    if args.id:
        wanted = set(args.id)
        casos = [c for c in casos if c.get("id") in wanted]

    resultados: list[dict] = []
    for caso in casos:
        r = _avaliar_case(caso, args.base_url, modo="parser", apenas_principal=bool(args.apenas_principal))
        resultados.append(
            {
                "base_url": r.base_url,
                "case_id": r.case_id,
                "ok": r.ok,
                "fail": r.fail,
                "peso_total": r.peso_total,
                "peso_perdido": r.peso_perdido,
                "extraido": r.extraido,
                "checks": r.checks,
                "error": r.error,
            }
        )

    Path(args.out).write_text(json.dumps({"resultados": resultados}, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"OK: wrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
