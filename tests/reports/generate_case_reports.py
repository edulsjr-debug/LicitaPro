from __future__ import annotations

import html
import json
from datetime import datetime
from pathlib import Path


HERE = Path(__file__).parent


def _esc(x) -> str:
    return html.escape("" if x is None else str(x))


def _fmt_jsonish(x) -> str:
    if isinstance(x, (dict, list)):
        return json.dumps(x, ensure_ascii=False)
    return "" if x is None else str(x)


def _read_report(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _case_from_report(report: dict) -> dict:
    casos = report.get("casos") or report.get("fixtures") or []
    if not casos:
        raise ValueError("relatório sem casos")
    if len(casos) != 1:
        # gerador é por-caso; se vier múltiplos, pega o primeiro.
        return casos[0]
    return casos[0]


def _render_case_html(case: dict, report: dict) -> str:
    checks = case.get("checks") or []
    arquivos = case.get("arquivos") or []
    extraido = case.get("extraido") or {}

    def get(k: str):
        return extraido.get(k) if isinstance(extraido, dict) else None

    objeto = get("objeto")
    if isinstance(objeto, str) and len(objeto) > 700:
        objeto = objeto[:700] + "..."
    docs = get("documentos_habilitacao")
    if isinstance(docs, list):
        docs_preview = "; ".join(str(x) for x in docs[:8])
        if len(docs) > 8:
            docs_preview += f" ... (+{len(docs) - 8})"
    else:
        docs_preview = docs

    ficha_md = get("ficha")
    if isinstance(ficha_md, str) and len(ficha_md) > 20000:
        ficha_md = ficha_md[:20000] + "\n\n[...ficha truncada...]\n"

    rows = []
    for chk in checks:
        tipo = chk.get("tipo", "")
        campo = chk.get("campo", "")
        peso = chk.get("peso", "")
        ok = chk.get("ok", False)
        valor = _fmt_jsonish(chk.get("valor_real"))
        if tipo == "esperado":
            esperado = _fmt_jsonish(chk.get("regra"))
        else:
            esperado = _fmt_jsonish(chk.get("proibidos"))
        rows.append(
            f"<tr class=\"{'ok' if ok else 'fail'}\">"
            f"<td>{_esc(tipo)}</td>"
            f"<td>{_esc(campo)}</td>"
            f"<td style=\"text-align:right\">{_esc(peso)}</td>"
            f"<td class=\"mono\">{_esc(valor)}</td>"
            f"<td class=\"mono\">{_esc(esperado)}</td>"
            f"<td style=\"text-align:center\">{('S' if ok else 'N')}</td>"
            f"</tr>"
        )

    arqs_rows = []
    for a in arquivos:
        arqs_rows.append(
            "<tr>"
            f"<td class=\"mono\">{_esc(a.get('arquivo'))}</td>"
            f"<td>{_esc(a.get('tipo'))}</td>"
            f"<td style=\"text-align:right\">{_esc(a.get('chars'))}</td>"
            "</tr>"
        )

    gen_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return f"""<!doctype html>
<html lang="pt-BR">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Relatório — {_esc(case.get('id'))}</title>
  <style>
    :root {{
      --fg: #111827;
      --muted: #6b7280;
      --border: #e5e7eb;
      --ok: #166534;
      --fail: #991b1b;
      --bg: #ffffff;
      --bg2: #f9fafb;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      padding: 28px;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Arial, sans-serif;
      color: var(--fg);
      background: var(--bg);
    }}
    h1 {{ font-size: 18px; margin: 0 0 6px; }}
    .sub {{ color: var(--muted); font-size: 12px; margin-bottom: 14px; }}
    .grid {{
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 12px;
      margin: 12px 0 18px;
    }}
    .card {{
      border: 1px solid var(--border);
      border-radius: 10px;
      padding: 12px 14px;
      background: var(--bg2);
    }}
    .kv {{ display: grid; grid-template-columns: 160px 1fr; gap: 6px 10px; font-size: 12px; }}
    .k {{ color: var(--muted); }}
    .mono {{ font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, "Liberation Mono", monospace; font-size: 11px; white-space: pre-wrap; }}
    table {{
      width: 100%;
      border-collapse: collapse;
      font-size: 12px;
    }}
    th, td {{
      border: 1px solid var(--border);
      padding: 8px 8px;
      vertical-align: top;
    }}
    th {{ background: #f3f4f6; text-align: left; }}
    tr.ok td:last-child {{ color: var(--ok); font-weight: 700; }}
    tr.fail td:last-child {{ color: var(--fail); font-weight: 700; }}
    .section-title {{ margin: 18px 0 8px; font-size: 13px; font-weight: 700; }}
  </style>
</head>
<body>
  <h1>Relatório de Caso — {_esc(case.get('id'))}</h1>
  <div class="sub">
    {_esc(case.get('descricao'))} · gerado em {gen_at}
  </div>

  <div class="grid">
    <div class="card">
      <div class="kv">
        <div class="k">Status</div><div>{_esc(case.get('status'))}</div>
        <div class="k">Confiança final</div><div>{_esc(case.get('confianca_final'))}</div>
        <div class="k">Score final</div><div>{_esc(case.get('score_final'))}</div>
        <div class="k">Peso total</div><div>{_esc(case.get('peso_total'))}</div>
        <div class="k">Peso perdido</div><div>{_esc(case.get('peso_perdido'))}</div>
      </div>
    </div>
    <div class="card">
      <div class="kv">
        <div class="k">Arquivo principal</div><div class="mono">{_esc(case.get('arquivo_principal'))}</div>
        <div class="k">Fonte</div><div>{_esc(case.get('fonte', report.get('versao_gabarito', '')))}</div>
        <div class="k">PDF/Path</div><div class="mono">{_esc(case.get('pdf_path'))}</div>
        <div class="k">Tamanho (bytes)</div><div>{_esc(case.get('tamanho_bytes'))}</div>
      </div>
    </div>
  </div>

  <div class="section-title">Extracao (parser)</div>
  <div class="card">
    <div class="kv">
      <div class="k">Numero / Processo</div><div class="mono">{_esc(get('numero_edital'))}</div>
      <div class="k">Orgao</div><div class="mono">{_esc(get('orgao'))}</div>
      <div class="k">Modalidade</div><div>{_esc(get('modalidade'))}</div>
      <div class="k">CNPJ</div><div class="mono">{_esc(get('cnpj'))}</div>
      <div class="k">Valor</div><div>{_esc(get('valor'))}</div>
      <div class="k">Data de abertura</div><div>{_esc(get('data_abertura'))}</div>
      <div class="k">Prazo vigencia</div><div>{_esc(get('prazo_vigencia'))}</div>
      <div class="k">Criterio julgamento</div><div>{_esc(get('criterio_julgamento'))}</div>
      <div class="k">Segmento</div><div>{_esc(get('segmento'))}</div>
      <div class="k">Faltantes</div><div class="mono">{_esc(get('faltantes'))}</div>
      <div class="k">Objeto</div><div class="mono">{_esc(objeto)}</div>
      <div class="k">Docs habilitacao</div><div class="mono">{_esc(docs_preview)}</div>
    </div>
  </div>

  <div class="section-title">Arquivos do Caso</div>
  <table>
    <thead>
      <tr><th>Arquivo</th><th>Tipo</th><th style="text-align:right">Chars</th></tr>
    </thead>
    <tbody>
      {''.join(arqs_rows) if arqs_rows else '<tr><td colspan="3" class="mono">(sem metadados)</td></tr>'}
    </tbody>
  </table>

  <div class="section-title">Checagens</div>
  <table>
    <thead>
      <tr>
        <th>Tipo</th>
        <th>Campo</th>
        <th style="text-align:right">Peso</th>
        <th>Extraído</th>
        <th>Esperado / Proibido</th>
        <th style="text-align:center">OK</th>
      </tr>
    </thead>
    <tbody>
      {''.join(rows) if rows else '<tr><td colspan="6" class="mono">(sem gabarito / sem checks)</td></tr>'}
    </tbody>
  </table>

  <div class="section-title">Ficha (parser)</div>
  <div class="card mono">{_esc(ficha_md)}</div>
</body>
</html>
"""


def main() -> int:
    json_files = sorted(HERE.glob("*.json"))
    if not json_files:
        raise SystemExit("Nenhum .json encontrado em tests/reports")

    out_dir = HERE
    for jf in json_files:
        report = _read_report(jf)
        case = _case_from_report(report)
        html_text = _render_case_html(case, report)
        out_path = out_dir / (jf.stem + ".html")
        out_path.write_text(html_text, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
