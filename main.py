import io
import json
import os
import re
import uuid
from pathlib import Path

import openai
import openpyxl
import pdfplumber
import docx
from dotenv import load_dotenv

from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

load_dotenv()

app = FastAPI(title="Proxy Licitação")

import datetime

LIMITE_DIARIO = 20  # análises por dia

_stats = {
    "total_analises": 0,
    "tokens_input_total": 0,
    "tokens_output_total": 0,
    "custo_usd_total": 0.0,
    "por_provedor": {},
    "hoje": datetime.date.today().isoformat(),
    "analises_hoje": 0,
}

# custo em USD por 1M tokens (input, output)
_CUSTO = {
    "gpt-4.1-nano":                           (0.10,  0.40),  # mais barato
    "gpt-4o-mini":                            (0.15,  0.60),
    "google/gemma-3-27b-it:free":             (0.0,   0.0),
    "meta-llama/llama-3.3-70b-instruct:free": (0.0,   0.0),
    "google/gemma-4-26b-a4b-it:free":         (0.0,   0.0),
    "nvidia/nemotron-3-super-120b-a12b:free": (0.0,   0.0),
    "google/gemma-3-12b-it:free":             (0.0,   0.0),
    "llama-3.3-70b-versatile":                (0.0,   0.0),
}

_openai = openai.AsyncOpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
)
_openrouter = openai.AsyncOpenAI(
    api_key=os.getenv("OPENROUTER_API_KEY"),
    base_url="https://openrouter.ai/api/v1",
)
_groq = openai.AsyncOpenAI(
    api_key=os.getenv("GROQ_API_KEY"),
    base_url="https://api.groq.com/openai/v1",
)
_groq2 = openai.AsyncOpenAI(
    api_key=os.getenv("GROQ_API_KEY2"),
    base_url="https://api.groq.com/openai/v1",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

SYSTEM_PROMPT = """Você é um especialista em licitações públicas brasileiras.
REGRA ABSOLUTA: comece a resposta IMEDIATAMENTE com "## FICHA DE LICITAÇÃO" — ZERO introduções, ZERO raciocínio, ZERO explicações. Apenas a ficha em Markdown.
Se um dado não constar no texto, escreva "Não informado".
Calcule o Valor Total de cada item (Qtd × Valor Unit.).
Siga EXATAMENTE esta estrutura:

## FICHA DE LICITAÇÃO

| Campo | Valor |
|---|---|
| **Nº / Processo** | ... |
| **Órgão** | ... |
| **Modalidade** | ... |
| **Critério de Julgamento** | ... |
| **Valor Estimado Total** | R$ ... |
| **Vigência do Contrato** | ... |
| **Abertura das Propostas** | ... |
| **Prazo para Envio de Proposta** | ... |

## Objeto
[descrição completa do objeto licitado]

## Condições Financeiras
- **Garantia Contratual:** ...
- **Prazo de Pagamento:** ...
- **Patrimônio Líquido Mínimo:** ...
- **Capital Social Mínimo:** ...

## Posto de Atendimento
[local/endereço onde os serviços serão prestados ou as entregas realizadas]

## Contato do Órgão
[e-mail e telefone do responsável]

## Itens a Cotar

| # | Descrição | Unid. | Qtd. | Valor Unit. | Valor Total |
|---|-----------|-------|------|-------------|-------------|
| 1 | ... | ... | ... | R$ ... | R$ ... |

## Modelo de Proposta
[tipo de taxa, o que é cotado, como lançar, observações importantes]

## Documentos de Habilitação

### Jurídica
- ...

### Fiscal e Trabalhista
- ...

### Econômico-Financeira
- ...

### Técnica
- ...

### Outras Exigências
- ...

## ⚠️ Alertas
> [ponto crítico relevante para a decisão de participar]

> [próximo alerta, se houver]"""

USER_TEMPLATE = "Analise o seguinte edital ({num_docs} documento(s)) e gere a ficha:\n\n{texto}"

HTML_PAGE = """<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>LicitaPro — Análise de Editais</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
<style>
:root{
  --brand-900:#061A33;--brand-800:#0A2540;--brand-700:#0E335A;
  --brand-600:#1E4FA0;--brand-500:#2F6FE0;--brand-400:#5C90EE;
  --brand-300:#8FB3F4;--brand-200:#C5D7F9;--brand-100:#E6EEFC;--brand-50:#F4F8FE;
  --ink-900:#111827;--ink-800:#1F2937;--ink-700:#374151;--ink-600:#4B5563;
  --ink-500:#6B7280;--ink-400:#9CA3AF;--ink-300:#D1D5DB;--ink-200:#E5E7EB;
  --ink-150:#EEF0F3;--ink-100:#F3F4F6;--ink-50:#F9FAFB;--ink-0:#FFFFFF;
  --success-700:#166534;--success-500:#22C55E;--success-100:#DCFCE7;
  --warn-700:#92400E;--warn-500:#F59E0B;--warn-100:#FEF3C7;--warn-50:#FFFBEB;
  --danger-700:#991B1B;--danger-500:#EF4444;--danger-100:#FEE2E2;--danger-50:#FEF2F2;
  --bg:#FFFFFF;--bg-subtle:#FAFBFC;
  --surface:var(--ink-0);--surface-2:var(--ink-50);--surface-3:var(--ink-100);
  --fg-1:var(--ink-900);--fg-2:var(--ink-600);--fg-3:var(--ink-500);--fg-4:var(--ink-400);
  --border:var(--ink-200);--border-subtle:var(--ink-150);
  --accent:var(--brand-500);--accent-hover:var(--brand-600);--accent-soft:var(--brand-50);
  --font-sans:'Inter',-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;
  --font-mono:'JetBrains Mono',Menlo,Consolas,monospace;
  --radius-sm:6px;--radius-md:10px;--radius-lg:14px;--radius-xl:20px;--radius-full:9999px;
  --shadow-xs:0 1px 2px rgba(11,15,20,.04);
  --shadow-sm:0 1px 2px rgba(11,15,20,.04),0 1px 3px rgba(11,15,20,.06);
  --shadow-md:0 4px 8px -2px rgba(11,15,20,.06),0 2px 4px -2px rgba(11,15,20,.04);
  --shadow-lg:0 12px 24px -8px rgba(11,15,20,.10),0 4px 8px -4px rgba(11,15,20,.06);
  --shadow-xl:0 24px 48px -12px rgba(11,15,20,.18);
  --ease-out:cubic-bezier(0.22,1,0.36,1);
  --dur-fast:120ms;--dur-base:200ms;--dur-slow:320ms;
}
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:var(--font-sans);background:var(--bg-subtle);color:var(--fg-1);min-height:100vh;-webkit-font-smoothing:antialiased}

/* Nav */
nav{position:sticky;top:0;z-index:100;background:rgba(255,255,255,.72);backdrop-filter:blur(20px) saturate(180%);-webkit-backdrop-filter:blur(20px) saturate(180%);border-bottom:1px solid var(--border-subtle)}
.nav-inner{max-width:880px;margin:0 auto;padding:0 24px;height:56px;display:flex;align-items:center;justify-content:space-between;gap:16px}
.logo{font-size:17px;font-weight:700;color:var(--ink-900);letter-spacing:-.025em;user-select:none}
.logo-dot{color:var(--brand-500)}
.nav-actions{display:flex;gap:8px}
.btn-ghost{display:inline-flex;align-items:center;gap:6px;padding:7px 13px;border-radius:var(--radius-md);border:1px solid var(--border);background:transparent;color:var(--fg-2);font-size:13px;font-weight:500;font-family:var(--font-sans);cursor:pointer;transition:background var(--dur-fast) var(--ease-out),color var(--dur-fast) var(--ease-out)}
.btn-ghost:hover{background:var(--ink-50);color:var(--fg-1)}
.btn-ghost svg{flex-shrink:0}
.btn-ghost .lbl{display:inline}

/* Layout */
main{max-width:880px;margin:0 auto;padding:32px 24px 64px}

/* Card */
.card{background:var(--surface);border:1px solid var(--border);border-radius:var(--radius-lg);padding:32px;box-shadow:var(--shadow-sm);margin-bottom:20px}

/* Dropzone */
.dropzone{border:1.5px dashed var(--brand-300);border-radius:var(--radius-md);padding:48px 24px;text-align:center;cursor:pointer;transition:background var(--dur-fast) var(--ease-out),border-color var(--dur-fast) var(--ease-out);background:var(--brand-50);user-select:none}
.dropzone:hover,.dropzone.over{background:var(--brand-100);border-color:var(--brand-400)}
.dz-icon{color:var(--brand-400);margin:0 auto 16px;display:block}
.dz-title{font-size:15px;font-weight:600;color:var(--ink-800);margin-bottom:4px}
.dz-sub{font-size:14px;color:var(--fg-3)}
.dz-hint{font-size:12px;color:var(--fg-4);margin-top:8px}
#file-input,#file-input-imp{display:none}

/* File list */
.files-list{margin-top:14px;display:flex;flex-direction:column;gap:8px}
.f-item{display:flex;align-items:center;gap:10px;padding:10px 14px;background:var(--brand-50);border:1px solid var(--brand-100);border-radius:var(--radius-sm);font-size:13px;color:var(--ink-800)}
.f-item .f-name{flex:1;min-width:0;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.f-item .f-size{color:var(--fg-4);font-family:var(--font-mono);font-size:11px;font-variant-numeric:tabular-nums;white-space:nowrap}
.f-item .rm{margin-left:4px;cursor:pointer;color:var(--fg-4);border:none;background:none;padding:2px;border-radius:4px;line-height:0;transition:color var(--dur-fast)}
.f-item .rm:hover{color:var(--danger-500)}

/* Buttons */
.btn-primary{display:flex;align-items:center;justify-content:center;gap:8px;width:100%;margin-top:20px;padding:13px 24px;background:var(--brand-500);color:#fff;border:none;border-radius:var(--radius-md);font-size:15px;font-weight:600;font-family:var(--font-sans);cursor:pointer;transition:background var(--dur-fast) var(--ease-out),transform 80ms}
.btn-primary:hover:not(:disabled){background:var(--brand-600)}
.btn-primary:active:not(:disabled){transform:scale(.98)}
.btn-primary:disabled{background:var(--ink-300);cursor:not-allowed}
.btn-primary:focus-visible{outline:none;box-shadow:0 0 0 3px rgba(47,111,224,.25)}
.btn-success{background:#166534}.btn-success:hover:not(:disabled){background:#14532d}
.btn-sm{display:inline-flex;align-items:center;gap:6px;padding:8px 14px;border-radius:var(--radius-sm);border:1px solid var(--border);background:var(--surface);color:var(--fg-2);font-size:13px;font-weight:500;font-family:var(--font-sans);cursor:pointer;transition:background var(--dur-fast),color var(--dur-fast)}
.btn-sm:hover{background:var(--ink-50);color:var(--fg-1)}

/* Error */
.err{background:var(--danger-50);border:1px solid var(--danger-100);border-radius:var(--radius-sm);padding:12px 16px;color:var(--danger-700);display:none;margin-top:14px;font-size:13px}

/* Import section */
.import-toggle{margin-top:24px;padding-top:20px;border-top:1px solid var(--border-subtle);cursor:pointer;display:flex;align-items:center;gap:8px;color:var(--brand-500);font-size:13px;font-weight:500;user-select:none;transition:color var(--dur-fast)}
.import-toggle:hover{color:var(--brand-600)}
.import-arrow{transition:transform var(--dur-base) var(--ease-out);display:inline-flex}
.import-sub-card{margin-top:16px;padding:24px;border:1px solid var(--border);border-radius:var(--radius-md);background:var(--bg-subtle)}
.import-or{text-align:center;color:var(--fg-4);font-size:12px;margin:16px 0 12px;position:relative}
.import-or::before,.import-or::after{content:'';position:absolute;top:50%;width:calc(50% - 20px);height:1px;background:var(--border)}
.import-or::before{left:0}.import-or::after{right:0}
textarea{width:100%;padding:10px 12px;border:1px solid var(--border);border-radius:var(--radius-sm);font-size:13px;font-family:var(--font-sans);resize:vertical;outline:none;background:var(--surface);color:var(--fg-1);transition:border-color var(--dur-fast)}
textarea:focus{border-color:var(--brand-400);box-shadow:0 0 0 3px rgba(47,111,224,.12)}
textarea::placeholder{color:var(--fg-4)}

/* Loading */
.loading{display:none;padding:40px 32px;text-align:center}
@keyframes shimmer{0%{background-position:-600px 0}100%{background-position:600px 0}}
.shimmer-line{height:11px;border-radius:var(--radius-full);background:linear-gradient(90deg,var(--ink-100) 25%,var(--ink-150) 50%,var(--ink-100) 75%);background-size:1200px 100%;animation:shimmer 1.4s ease infinite;margin-bottom:10px}
.loading-label{font-size:14px;color:var(--fg-3);margin-top:20px}
.loading-sub{font-size:12px;color:var(--fg-4);margin-top:6px}

/* Result */
.result{display:none}
.result-header{display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:12px;margin-bottom:24px;padding-bottom:20px;border-bottom:1px solid var(--border)}
.result-title{font-size:17px;font-weight:600;color:var(--ink-900);letter-spacing:-.01em}
.r-actions{display:flex;gap:8px}
.result-divider{margin:28px 0;border:none;border-top:1px solid var(--border)}

/* Ficha (markdown) */
.ficha{line-height:1.7;font-size:14px;color:var(--fg-1)}
.ficha h2{font-size:11px;font-weight:600;color:var(--fg-3);letter-spacing:.08em;text-transform:uppercase;margin:28px 0 12px;padding-bottom:8px;border-bottom:1px solid var(--border)}
.ficha h2:first-child{margin-top:0}
.ficha h3{font-size:15px;font-weight:600;color:var(--ink-800);margin:20px 0 8px}
.ficha h4{font-size:14px;font-weight:600;color:var(--ink-700);margin:14px 0 6px}
.ficha p{margin:6px 0;color:var(--fg-2)}
.ficha table{width:100%;border-collapse:collapse;margin:12px 0 16px;font-size:13px;border:1px solid var(--border);border-radius:var(--radius-sm);overflow:hidden}
.ficha th{background:var(--ink-50);font-weight:600;color:var(--fg-3);font-size:11px;text-transform:uppercase;letter-spacing:.06em;padding:9px 13px;text-align:left;border-bottom:1px solid var(--border)}
.ficha td{padding:9px 13px;border-bottom:1px solid var(--border-subtle);vertical-align:top}
.ficha tr:last-child td{border-bottom:none}
.ficha tr:hover td{background:var(--ink-50)}
.ficha table:first-of-type th{background:var(--brand-800);color:#fff;font-size:11px}
.ficha table:first-of-type td:first-child{font-weight:500;color:var(--ink-800);background:var(--brand-50);width:42%}
.ficha table:first-of-type tr:hover td{background:var(--brand-50)}
.ficha blockquote{border-left:3px solid var(--warn-500);padding:10px 16px;background:var(--warn-50);border-radius:0 var(--radius-sm) var(--radius-sm) 0;margin:12px 0;font-size:13px;color:var(--warn-700)}
.ficha ul,.ficha ol{padding-left:20px;margin:8px 0}
.ficha li{margin:4px 0;color:var(--fg-2)}
.ficha strong{color:var(--ink-900);font-weight:600}
.ficha code{font-family:var(--font-mono);font-size:.9em;background:var(--surface-3);padding:2px 5px;border-radius:4px}
.ficha hr{border:none;border-top:1px solid var(--border);margin:20px 0}

/* History panel */
#historico-overlay{position:fixed;inset:0;background:rgba(11,15,20,.4);z-index:200;display:none;justify-content:flex-end}
#historico-panel{background:var(--surface);width:min(480px,100vw);display:flex;flex-direction:column;height:100%;box-shadow:var(--shadow-xl);animation:slideIn var(--dur-slow) var(--ease-out)}
@keyframes slideIn{from{transform:translateX(100%)}to{transform:translateX(0)}}
@keyframes spin{to{transform:rotate(360deg)}}
.panel-head{background:var(--brand-800);color:#fff;padding:18px 20px;display:flex;justify-content:space-between;align-items:center;flex-shrink:0}
.panel-head-title{font-size:15px;font-weight:600;letter-spacing:-.01em}
.panel-head-actions{display:flex;gap:8px;align-items:center}
.btn-panel-action{background:rgba(255,255,255,.12);border:1px solid rgba(255,255,255,.25);color:#fff;padding:5px 11px;border-radius:var(--radius-sm);font-size:12px;font-family:var(--font-sans);cursor:pointer;transition:background var(--dur-fast);display:inline-flex;align-items:center;gap:5px}
.btn-panel-action:hover{background:rgba(255,255,255,.22)}
.btn-panel-close{background:none;border:none;color:rgba(255,255,255,.7);cursor:pointer;padding:4px;border-radius:4px;line-height:0;transition:color var(--dur-fast)}
.btn-panel-close:hover{color:#fff}
.h-busca-wrap{padding:16px 16px 8px;flex-shrink:0}
.h-busca{width:100%;padding:9px 13px;border:1px solid var(--border);border-radius:var(--radius-sm);font-size:13px;font-family:var(--font-sans);outline:none;color:var(--fg-1);background:var(--surface);transition:border-color var(--dur-fast)}
.h-busca:focus{border-color:var(--brand-400);box-shadow:0 0 0 3px rgba(47,111,224,.12)}
.h-busca::placeholder{color:var(--fg-4)}
#h-chips{padding:4px 16px 12px;display:flex;flex-wrap:wrap;gap:6px;flex-shrink:0}
.chip{padding:4px 12px;border-radius:var(--radius-full);font-size:12px;font-weight:500;cursor:pointer;background:var(--ink-100);color:var(--ink-700);border:1px solid var(--border);user-select:none;transition:background var(--dur-fast),border-color var(--dur-fast)}
.chip:hover{border-color:var(--brand-300)}
.chip-ativo{background:var(--brand-800)!important;color:#fff!important;border-color:var(--brand-800)!important}
.h-count{font-size:12px;color:var(--fg-4);padding:0 16px 8px;flex-shrink:0;font-variant-numeric:tabular-nums}
#h-lista{flex:1;overflow-y:auto;padding:4px 16px 24px}
.h-card{border:1px solid var(--border);border-radius:var(--radius-lg);padding:14px 16px;margin-bottom:10px;cursor:pointer;transition:box-shadow var(--dur-fast),border-color var(--dur-fast)}
.h-card:hover{box-shadow:var(--shadow-md);border-color:var(--brand-200)}
.h-card-top{display:flex;justify-content:space-between;align-items:center;margin-bottom:6px;gap:8px}
.h-badge{font-size:11px;font-weight:600;padding:3px 10px;border-radius:var(--radius-full);white-space:nowrap}
.h-data{color:var(--fg-4);font-size:11px;white-space:nowrap;font-variant-numeric:tabular-nums}
.h-orgao{font-weight:600;font-size:13px;color:var(--ink-900);margin-bottom:3px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.h-objeto{font-size:12px;color:var(--fg-3);margin-bottom:8px;line-height:1.5;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}
.h-card-foot{display:flex;justify-content:space-between;align-items:center}
.h-valor{font-size:12px;color:var(--success-700);font-weight:600;font-variant-numeric:tabular-nums}
.h-btn-pdf{display:inline-flex;align-items:center;gap:5px;background:transparent;color:var(--brand-500);border:1px solid var(--brand-200);padding:4px 11px;border-radius:var(--radius-sm);font-size:11px;font-weight:500;font-family:var(--font-sans);cursor:pointer;transition:background var(--dur-fast)}
.h-btn-pdf:hover{background:var(--brand-50);color:var(--brand-600)}
.h-vazio{text-align:center;color:var(--fg-4);padding:48px 0;font-size:14px}

/* Help panel */
#ajuda-overlay{position:fixed;inset:0;background:rgba(11,15,20,.4);z-index:200;display:none;justify-content:flex-end}
#ajuda-panel{background:var(--surface);width:min(520px,100vw);display:flex;flex-direction:column;height:100%;box-shadow:var(--shadow-xl);animation:slideIn var(--dur-slow) var(--ease-out)}
#ajuda-corpo{flex:1;overflow-y:auto;padding:8px 24px 32px}
.aj-sec{padding:20px 0;border-bottom:1px solid var(--border-subtle)}
.aj-sec:last-child{border-bottom:none}
.aj-titulo{font-size:13px;font-weight:600;color:var(--ink-800);margin-bottom:10px}
.aj-ul{padding-left:16px;font-size:13px;color:var(--fg-2);line-height:1.9}
.aj-ol{padding-left:16px;font-size:13px;color:var(--fg-2);line-height:2.1}
.aj-ul li,.aj-ol li{margin-bottom:2px}
.aj-chips{display:flex;flex-wrap:wrap;gap:6px}
.aj-chip{background:var(--brand-50);color:var(--brand-700);font-size:12px;padding:4px 11px;border-radius:var(--radius-full);font-weight:500;border:1px solid var(--brand-100)}
.aj-grid2{display:grid;grid-template-columns:1fr 1fr;gap:8px;font-size:13px;color:var(--fg-2);line-height:1.9}
#ajuda-corpo a{color:var(--brand-500);font-weight:500}
#ajuda-corpo a:hover{opacity:.7}

/* Print */
@media print{
  @page{size:A4 portrait;margin:1.8cm 2cm}
  *{-webkit-print-color-adjust:exact!important;print-color-adjust:exact!important}
  nav,.card:first-child,.r-actions,#nova-analise{display:none!important}
  .result{display:block!important}
  .card{box-shadow:none;padding:0;margin:0;border-radius:0;border:none}
  body{background:#fff;font-size:10pt}
  .ficha{font-size:9.5pt;line-height:1.55}
  .ficha h2{font-size:9pt;margin:14pt 0 6pt;page-break-after:avoid;border-bottom:.5pt solid #ccc;text-transform:uppercase;letter-spacing:.06em;color:#6b7280;font-weight:600}
  .ficha h3{font-size:10pt;margin:8pt 0 4pt;page-break-after:avoid}
  .ficha table{font-size:8.5pt;width:100%;table-layout:fixed;word-wrap:break-word}
  .ficha th,.ficha td{padding:4pt 6pt;border:.5pt solid #ccc}
  .ficha th{background:#f0f0f0!important}
  .ficha table:first-of-type th{background:#0A2540!important;color:#fff!important}
  .ficha table:first-of-type td:first-child{background:#F4F8FE!important;font-weight:600}
  .ficha tr{page-break-inside:avoid}
  .ficha blockquote{font-size:8.5pt;padding:4pt 8pt;page-break-inside:avoid;background:#FFFBEB!important;border-left:2pt solid #F59E0B}
  .ficha ul,.ficha ol{padding-left:14pt}
  .ficha hr{margin:10pt 0;border-top:.5pt solid #ddd}
  main{max-width:100%;padding:0;margin:0}
}

@media(max-width:600px){
  .nav-inner{padding:0 16px}
  main{padding:20px 16px 48px}
  .card{padding:20px}
  .dropzone{padding:36px 16px}
  .btn-ghost .lbl{display:none}
  #historico-panel,#ajuda-panel{width:100vw}
  .aj-grid2{grid-template-columns:1fr}
}
</style>
</head>
<body>

<nav>
  <div class="nav-inner">
    <span class="logo">Licita<span class="logo-dot">Pro</span></span>
    <div class="nav-actions">
      <button class="btn-ghost" onclick="abrirAjuda()">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"/><path d="M12 17h.01"/></svg>
        <span class="lbl">Ajuda</span>
      </button>
      <button class="btn-ghost" onclick="abrirHistorico()">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round"><path d="M21 8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16Z"/><path d="m3.3 7 8.7 5 8.7-5"/><path d="M12 22V12"/></svg>
        <span class="lbl">Outras análises</span>
      </button>
    </div>
  </div>
</nav>

<main>
  <div class="card" id="upload-card">
    <div class="dropzone" id="dropzone">
      <svg class="dz-icon" width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" x2="12" y1="3" y2="15"/></svg>
      <p class="dz-title">Arraste o arquivo do edital aqui</p>
      <p class="dz-sub">ou clique para selecionar</p>
      <p class="dz-hint">PDF · DOCX · XLSX · XLS · TXT &nbsp;·&nbsp; múltiplos arquivos</p>
    </div>
    <input type="file" id="file-input" accept=".pdf,.docx,.xlsx,.xls,.txt" multiple>
    <div class="files-list" id="files-list"></div>
    <div class="err" id="err"></div>
    <button class="btn-primary" id="btn" disabled>Analisar edital</button>

    <div class="import-toggle" onclick="toggleImport()">
      <span class="import-arrow" id="imp-arrow">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m9 18 6-6-6-6"/></svg>
      </span>
      Importar fichas já realizadas
    </div>

    <div id="import-section" style="display:none">
      <div class="import-sub-card">
        <div class="dropzone" id="dropzone-imp" style="padding:28px 20px">
          <svg style="color:var(--ink-400);margin:0 auto 12px;display:block" width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" x2="12" y1="3" y2="15"/></svg>
          <p class="dz-title" style="font-size:14px">Arraste as fichas prontas aqui</p>
          <p class="dz-sub">ou clique para selecionar</p>
          <p class="dz-hint">PDF · DOCX · TXT · o sistema identifica automaticamente</p>
        </div>
        <input type="file" id="file-input-imp" accept=".pdf,.docx,.xlsx,.xls,.txt" multiple>
        <div class="files-list" id="files-list-imp"></div>
        <div class="err" id="err-imp"></div>
        <button class="btn-primary btn-success" id="btn-imp" disabled style="margin-top:14px">Importar para o histórico</button>
        <div class="import-or">ou</div>
        <textarea id="imp-textarea" rows="4" placeholder="Cole aqui o conteúdo da ficha…"></textarea>
        <button class="btn-primary btn-success" id="btn-imp-txt" style="margin-top:10px" onclick="importarTexto()">Importar texto colado</button>
      </div>
    </div>
  </div>

  <div class="card loading" id="loading">
    <div class="shimmer-line" style="width:80%"></div>
    <div class="shimmer-line" style="width:65%"></div>
    <div class="shimmer-line" style="width:90%"></div>
    <div class="shimmer-line"></div>
    <p class="loading-label">Analisando o edital, aguarde…</p>
    <p class="loading-sub">Pode levar até 2 minutos</p>
  </div>

  <div class="card result" id="result">
    <div class="result-header">
      <span class="result-title">Ficha de licitação</span>
      <div class="r-actions">
        <button class="btn-sm" onclick="copiar()">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round"><rect width="14" height="14" x="8" y="8" rx="2" ry="2"/><path d="M4 16c-1.1 0-2-.9-2-2V4c0-1.1.9-2 2-2h10c1.1 0 2 .9 2 2"/></svg>
          Copiar
        </button>
        <button class="btn-sm" onclick="window.print()">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round"><polyline points="6 9 6 2 18 2 18 9"/><path d="M6 18H4a2 2 0 0 1-2-2v-5a2 2 0 0 1 2-2h16a2 2 0 0 1 2 2v5a2 2 0 0 1-2 2h-2"/><rect width="12" height="8" x="6" y="14"/></svg>
          Imprimir / PDF
        </button>
      </div>
    </div>
    <div class="ficha" id="ficha"></div>
    <hr class="result-divider">
    <button class="btn-primary btn-success" id="nova-analise" onclick="novaAnalise()">
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12h14"/><path d="M12 5v14"/></svg>
      Nova análise
    </button>
  </div>
</main>

<div id="ajuda-overlay" onclick="if(event.target===this)fecharAjuda()">
  <div id="ajuda-panel">
    <div class="panel-head">
      <span class="panel-head-title">Como usar o sistema</span>
      <button class="btn-panel-close" onclick="fecharAjuda()">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M18 6 6 18"/><path d="m6 6 12 12"/></svg>
      </button>
    </div>
    <div id="ajuda-corpo">
      <div class="aj-sec">
        <div class="aj-titulo">Como analisar um edital</div>
        <ol class="aj-ol">
          <li>Arraste o arquivo do edital para a área pontilhada <b>ou</b> clique nela para selecionar</li>
          <li>Pode enviar <b>mais de um arquivo</b> ao mesmo tempo (ex: edital + anexos)</li>
          <li>Clique em <b>Analisar edital</b> e aguarde — pode levar até 2 minutos</li>
          <li>A ficha aparece automaticamente na tela</li>
        </ol>
      </div>
      <div class="aj-sec">
        <div class="aj-titulo">Formatos aceitos</div>
        <div class="aj-chips">
          <span class="aj-chip">PDF</span><span class="aj-chip">DOCX</span>
          <span class="aj-chip">XLSX</span><span class="aj-chip">XLS</span><span class="aj-chip">TXT</span>
        </div>
      </div>
      <div class="aj-sec">
        <div class="aj-titulo">O que a ficha contém</div>
        <div class="aj-grid2">
          <div>· Nº e Processo<br>· Órgão contratante<br>· Modalidade e Critério<br>· Valor Estimado<br>· Vigência do contrato<br>· Datas de abertura e proposta</div>
          <div>· Garantia e Pagamento<br>· Patrimônio Líquido mínimo<br>· Capital Social mínimo<br>· Itens a cotar (tabela)<br>· Documentos de habilitação<br>· Alertas e pontos críticos</div>
        </div>
      </div>
      <div class="aj-sec">
        <div class="aj-titulo">Outras análises (histórico)</div>
        <ul class="aj-ul">
          <li>Todas as análises ficam salvas automaticamente</li>
          <li>Filtre por <b>segmento</b> ou use a <b>busca</b> por órgão/objeto</li>
          <li>Clique em qualquer análise para ver a ficha completa</li>
          <li>Clique em <b>PDF</b> para abrir e exportar como PDF</li>
        </ul>
      </div>
      <div class="aj-sec">
        <div class="aj-titulo">Segmentos detectados automaticamente</div>
        <div class="aj-chips">
          <span class="aj-chip">Saúde</span><span class="aj-chip">Educação</span>
          <span class="aj-chip">Obras e Infraestrutura</span><span class="aj-chip">Alimentação</span>
          <span class="aj-chip">Tecnologia e TI</span><span class="aj-chip">Transporte</span>
          <span class="aj-chip">Viagens e Passagens</span><span class="aj-chip">Eventos e Capacitação</span>
          <span class="aj-chip">Limpeza e Conservação</span><span class="aj-chip">Mobiliário e Escritório</span>
          <span class="aj-chip">Segurança</span><span class="aj-chip">Outros</span>
        </div>
      </div>
      <div class="aj-sec">
        <div class="aj-titulo">Informações do sistema</div>
        <ul class="aj-ul">
          <li><b>Limite diário:</b> 20 análises por dia — reinicia à meia-noite</li>
          <li><b>Editais pequenos</b> (até ~15 mil caracteres) usam provedores <b>gratuitos</b> automaticamente</li>
          <li><b>Editais grandes</b> usam o OpenAI como prioridade para melhor qualidade</li>
          <li>Acesse <a href="/status" target="_blank"><b>/status</b></a> para ver consumo, custos e histórico por segmento</li>
        </ul>
      </div>
      <div class="aj-sec">
        <div class="aj-titulo">Imprimir / Exportar PDF</div>
        <ul class="aj-ul">
          <li>Clique em <b>Imprimir / PDF</b> na tela da ficha</li>
          <li>No diálogo do navegador, escolha <b>Salvar como PDF</b></li>
          <li>O layout foi otimizado para impressão em A4</li>
        </ul>
      </div>
    </div>
  </div>
</div>

<div id="historico-overlay" onclick="fecharSeFora(event)">
  <div id="historico-panel">
    <div class="panel-head">
      <span class="panel-head-title">Outras análises</span>
      <div class="panel-head-actions">
        <button class="btn-panel-action btn-reclassificar" onclick="reclassificar()" title="Reclassificar segmentos">
          <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 12a9 9 0 0 1 9-9 9.75 9.75 0 0 1 6.74 2.74L21 8"/><path d="M21 3v5h-5"/><path d="M21 12a9 9 0 0 1-9 9 9.75 9.75 0 0 1-6.74-2.74L3 16"/><path d="M8 16H3v5"/></svg>
          Reclassificar
        </button>
        <button class="btn-panel-close btn-hfechar" onclick="fecharHistorico()">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M18 6 6 18"/><path d="m6 6 12 12"/></svg>
        </button>
      </div>
    </div>
    <div class="h-busca-wrap">
      <input class="h-busca" id="h-busca" placeholder="Buscar por órgão ou objeto…" oninput="renderHistorico()">
    </div>
    <div id="h-chips"></div>
    <div class="h-count" id="h-count"></div>
    <div id="h-lista"><p class="h-vazio">Carregando…</p></div>
  </div>
</div>

<script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
<script>
const IC_FILE=`<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round"><path d="M15 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7Z"/><path d="M14 2v4a2 2 0 0 0 2 2h4"/></svg>`;
const IC_X=`<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M18 6 6 18"/><path d="m6 6 12 12"/></svg>`;
const IC_DL=`<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" x2="12" y1="3" y2="15"/></svg>`;
const IC_SPIN=`<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="animation:spin 1s linear infinite"><path d="M3 12a9 9 0 0 1 9-9 9.75 9.75 0 0 1 6.74 2.74L21 8"/><path d="M21 3v5h-5"/></svg>`;
const IC_RECLASSIFY=`<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 12a9 9 0 0 1 9-9 9.75 9.75 0 0 1 6.74 2.74L21 8"/><path d="M21 3v5h-5"/><path d="M21 12a9 9 0 0 1-9 9 9.75 9.75 0 0 1-6.74-2.74L3 16"/><path d="M8 16H3v5"/></svg>`;

const dropzone=document.getElementById('dropzone');
const fileInput=document.getElementById('file-input');
const filesList=document.getElementById('files-list');
const btn=document.getElementById('btn');
const errEl=document.getElementById('err');
const loading=document.getElementById('loading');
const resultEl=document.getElementById('result');
const fichaEl=document.getElementById('ficha');
let files=[];
let _fichaMarkdown='';

dropzone.addEventListener('click',()=>fileInput.click());
dropzone.addEventListener('dragover',e=>{e.preventDefault();dropzone.classList.add('over')});
dropzone.addEventListener('dragleave',()=>dropzone.classList.remove('over'));
dropzone.addEventListener('drop',e=>{e.preventDefault();dropzone.classList.remove('over');addFiles([...e.dataTransfer.files])});
fileInput.addEventListener('change',()=>{addFiles([...fileInput.files]);fileInput.value=''});

function addFiles(list){
  list.filter(f=>/\\.(pdf|docx|xlsx|xls|txt)$/i.test(f.name)).forEach(f=>files.push(f));
  render();
}
function remove(i){files.splice(i,1);render()}
function render(){
  filesList.innerHTML=files.map((f,i)=>`
    <div class="f-item">
      ${IC_FILE}
      <span class="f-name">${f.name}</span>
      <span class="f-size">${(f.size/1024).toFixed(0)} KB</span>
      <button class="rm" onclick="remove(${i})" title="Remover">${IC_X}</button>
    </div>`).join('');
  btn.disabled=files.length===0;
}

btn.addEventListener('click',async()=>{
  if(!files.length)return;
  errEl.style.display='none';
  document.getElementById('upload-card').style.display='none';
  loading.style.display='block';
  resultEl.style.display='none';
  try{
    const fd=new FormData();
    files.forEach(f=>fd.append('arquivos',f));
    const r=await fetch('/analisar/arquivo',{method:'POST',body:fd});
    const data=await r.json();
    if(!r.ok)throw new Error(data.detail||'Erro desconhecido');
    _fichaMarkdown=data.ficha;
    fichaEl.innerHTML=marked.parse(data.ficha);
    loading.style.display='none';
    resultEl.style.display='block';
  }catch(e){
    loading.style.display='none';
    document.getElementById('upload-card').style.display='block';
    errEl.textContent=e.message;
    errEl.style.display='block';
  }
});

function novaAnalise(){
  files=[];render();
  resultEl.style.display='none';
  document.getElementById('upload-card').style.display='block';
  errEl.style.display='none';
}

// ── Import ────────────────────────────────────────────────────────────────────
const dropzoneImp=document.getElementById('dropzone-imp');
const fileInputImp=document.getElementById('file-input-imp');
const filesListImp=document.getElementById('files-list-imp');
const btnImp=document.getElementById('btn-imp');
const errImp=document.getElementById('err-imp');
let filesImp=[];

function toggleImport(){
  const sec=document.getElementById('import-section');
  const arrow=document.getElementById('imp-arrow');
  const open=sec.style.display==='none';
  sec.style.display=open?'block':'none';
  arrow.style.transform=open?'rotate(90deg)':'rotate(0deg)';
}
dropzoneImp.addEventListener('click',()=>fileInputImp.click());
dropzoneImp.addEventListener('dragover',e=>{e.preventDefault();dropzoneImp.classList.add('over')});
dropzoneImp.addEventListener('dragleave',()=>dropzoneImp.classList.remove('over'));
dropzoneImp.addEventListener('drop',e=>{e.preventDefault();dropzoneImp.classList.remove('over');addFilesImp([...e.dataTransfer.files])});
fileInputImp.addEventListener('change',()=>{addFilesImp([...fileInputImp.files]);fileInputImp.value='';});

function addFilesImp(list){
  list.filter(f=>/\\.(pdf|docx|xlsx|xls|txt)$/i.test(f.name)).forEach(f=>filesImp.push(f));
  renderImp();
}
function removeImp(i){filesImp.splice(i,1);renderImp();}
function renderImp(){
  filesListImp.innerHTML=filesImp.map((f,i)=>`
    <div class="f-item">${IC_FILE}<span class="f-name">${f.name}</span>
    <span class="f-size">${(f.size/1024).toFixed(0)} KB</span>
    <button class="rm" onclick="removeImp(${i})">${IC_X}</button></div>`).join('');
  btnImp.disabled=filesImp.length===0;
}
btnImp.addEventListener('click',async()=>{
  if(!filesImp.length)return;
  errImp.style.display='none';
  btnImp.disabled=true;
  btnImp.textContent='Importando…';
  try{
    const fd=new FormData();
    filesImp.forEach(f=>fd.append('arquivos',f));
    const r=await fetch('/importar/arquivo',{method:'POST',body:fd});
    const data=await r.json();
    if(!r.ok)throw new Error(data.detail||'Erro desconhecido');
    const n=data.importados.length;
    const ig=data.ignorados.length;
    filesImp=[];renderImp();
    btnImp.textContent='Importar para o histórico';
    if(n>0){
      let msg=n+' ficha(s) importada(s) com sucesso!';
      if(ig) msg+='\\n\\n'+ig+' arquivo(s) ignorado(s):\\n'+data.ignorados.map(x=>'• '+x.arquivo+': '+x.motivo).join('\\n');
      alert(msg);
    } else {
      let motivos=data.ignorados.map(x=>'• '+x.arquivo+': '+x.motivo).join('\\n');
      alert('Nenhum arquivo importado.\\n\\n'+motivos);
    }
  }catch(e){
    errImp.textContent=e.message;
    errImp.style.display='block';
    btnImp.textContent='Importar para o histórico';
    btnImp.disabled=false;
  }
});

async function importarTexto(){
  const txt=document.getElementById('imp-textarea').value.trim();
  if(!txt){alert('Cole o texto da ficha antes de importar.');return;}
  const b=document.getElementById('btn-imp-txt');
  b.disabled=true;b.textContent='Importando…';
  try{
    const r=await fetch('/importar/texto',{method:'POST',
      headers:{'Content-Type':'application/json'},
      body:JSON.stringify({texto:txt,num_docs:1})});
    const d=await r.json();
    if(!r.ok)throw new Error(d.detail||'Erro');
    document.getElementById('imp-textarea').value='';
    b.textContent='Importar texto colado';b.disabled=false;
    alert('Ficha importada com sucesso!');
  }catch(e){
    b.textContent='Importar texto colado';b.disabled=false;
    alert(e.message);
  }
}

function copiar(){
  navigator.clipboard.writeText(_fichaMarkdown)
    .then(()=>alert('Ficha copiada (Markdown) para a área de transferência!'));
}

// ── Histórico ─────────────────────────────────────────────────────────────────
const SEG_CORES={
  'Saúde':{bg:'#DCFCE7',c:'#166534'},
  'Educação':{bg:'#DBEAFE',c:'#1E40AF'},
  'Obras e Infraestrutura':{bg:'#FEF3C7',c:'#92400E'},
  'Alimentação':{bg:'#FEE2E2',c:'#991B1B'},
  'Tecnologia e TI':{bg:'#EDE9FE',c:'#5B21B6'},
  'Transporte':{bg:'#CFFAFE',c:'#164E63'},
  'Viagens e Passagens':{bg:'#E0F2FE',c:'#0C4A6E'},
  'Eventos e Capacitação':{bg:'#FEF9C3',c:'#713F12'},
  'Limpeza e Conservação':{bg:'#F3E8FF',c:'#6B21A8'},
  'Mobiliário e Escritório':{bg:'#E0E7FF',c:'#3730A3'},
  'Segurança':{bg:'#FCE7F3',c:'#9D174D'},
  'Outros':{bg:'#F3F4F6',c:'#374151'}
};
function segStyle(seg){const s=SEG_CORES[seg]||SEG_CORES['Outros'];return `background:${s.bg};color:${s.c}`;}

let _hDados=[];
let _hSeg='';

async function abrirHistorico(){
  document.getElementById('historico-overlay').style.display='flex';
  document.getElementById('h-busca').value='';
  _hSeg='';
  document.getElementById('h-lista').innerHTML='<p class="h-vazio">Carregando…</p>';
  try{
    const r=await fetch('/historico');
    const data=await r.json();
    _hDados=data.historico;
    renderChips();
    renderHistorico();
  }catch(e){
    document.getElementById('h-lista').innerHTML='<p class="h-vazio">Erro ao carregar histórico.</p>';
  }
}

function fecharHistorico(){document.getElementById('historico-overlay').style.display='none';}
function fecharSeFora(e){if(e.target===document.getElementById('historico-overlay'))fecharHistorico();}
document.addEventListener('keydown',e=>{if(e.key==='Escape'){fecharHistorico();fecharAjuda();}});
function abrirAjuda(){document.getElementById('ajuda-overlay').style.display='flex';}
function fecharAjuda(){document.getElementById('ajuda-overlay').style.display='none';}

function renderChips(){
  const segs=['Todos',...new Set(_hDados.map(r=>r.segmento))];
  document.getElementById('h-chips').innerHTML=segs.map(s=>{
    const ativo=s===(_hSeg||'Todos');
    const estilo=(!ativo&&s!=='Todos')?`style="${segStyle(s)}"`:'' ;
    return `<span class="chip${ativo?' chip-ativo':''}" ${estilo} onclick="filtrarSeg('${s}')">${s}</span>`;
  }).join('');
}

function filtrarSeg(seg){_hSeg=seg==='Todos'?'':seg;renderChips();renderHistorico();}

function renderHistorico(){
  const busca=document.getElementById('h-busca').value.toLowerCase();
  const lista=_hDados.filter(r=>{
    const okSeg=!_hSeg||r.segmento===_hSeg;
    const okBusca=!busca||r.orgao.toLowerCase().includes(busca)||r.objeto.toLowerCase().includes(busca);
    return okSeg&&okBusca;
  });
  document.getElementById('h-count').textContent=
    lista.length?`${lista.length} análise${lista.length!==1?'s':''}`:' ';
  if(!lista.length){
    document.getElementById('h-lista').innerHTML='<p class="h-vazio">Nenhuma análise encontrada.</p>';
    return;
  }
  document.getElementById('h-lista').innerHTML=lista.map(r=>`
    <div class="h-card" onclick="verFicha('${r.id}')">
      <div class="h-card-top">
        <span class="h-badge" style="${segStyle(r.segmento)}">${r.segmento}</span>
        <span class="h-data">${fmtData(r.timestamp)}</span>
      </div>
      <div class="h-orgao" title="${r.orgao}">${r.orgao}</div>
      <div class="h-objeto">${r.objeto}</div>
      <div class="h-card-foot">
        <span class="h-valor">${r.valor}</span>
        <button class="h-btn-pdf" onclick="verFichaEImprimir('${r.id}',event)">${IC_DL} PDF</button>
      </div>
    </div>`).join('');
}

function fmtData(ts){
  const d=new Date(ts);
  return d.toLocaleDateString('pt-BR')+' '+d.toLocaleTimeString('pt-BR',{hour:'2-digit',minute:'2-digit'});
}

async function verFicha(id){
  try{
    const r=await fetch('/historico/'+id);
    const data=await r.json();
    _fichaMarkdown=data.ficha;
    fichaEl.innerHTML=marked.parse(data.ficha);
    fecharHistorico();
    document.getElementById('upload-card').style.display='none';
    loading.style.display='none';
    resultEl.style.display='block';
  }catch(e){alert('Erro ao carregar análise.');}
}

async function reclassificar(){
  const btn=document.querySelector('.btn-reclassificar');
  btn.innerHTML=IC_SPIN+' Aguarde';
  btn.disabled=true;
  try{
    const r=await fetch('/api/reclassificar',{method:'POST'});
    const d=await r.json();
    setTimeout(()=>{btn.innerHTML=IC_RECLASSIFY+' Reclassificar';btn.disabled=false;},2000);
    const r2=await fetch('/historico');
    const d2=await r2.json();
    _hDados=d2.historico;renderChips();renderHistorico();
    if(d.atualizados>0)alert(`${d.atualizados} análise(s) reclassificada(s) de ${d.total} no histórico.`);
  }catch(e){btn.innerHTML=IC_RECLASSIFY+' Reclassificar';btn.disabled=false;}
}

async function verFichaEImprimir(id,evt){
  evt.stopPropagation();
  await verFicha(id);
  setTimeout(()=>window.print(),350);
}
</script>
</body>
</html>"""


class AnalisarRequest(BaseModel):
    texto: str
    num_docs: int = 2


class AnalisarResponse(BaseModel):
    ficha: str


def extrair_texto(nome: str, conteudo: bytes) -> str:
    nome_lower = nome.lower()
    if nome_lower.endswith(".pdf"):
        with pdfplumber.open(io.BytesIO(conteudo)) as pdf:
            partes = []
            for p in pdf.pages:
                texto = p.extract_text() or ""
                if not texto.strip():
                    try:
                        words = p.extract_words(x_tolerance=5, y_tolerance=5)
                        if words:
                            texto = " ".join(w["text"] for w in words)
                    except Exception:
                        pass
                partes.append(texto)
        resultado = "\n".join(partes).strip()
        if not resultado:
            # último recurso: pdfminer.six diretamente
            try:
                from pdfminer.high_level import extract_text as _pm_et
                resultado = (_pm_et(io.BytesIO(conteudo)) or "").strip()
            except Exception:
                pass
        return resultado
    if nome_lower.endswith(".docx"):
        doc = docx.Document(io.BytesIO(conteudo))
        return "\n".join(p.text for p in doc.paragraphs)
    if nome_lower.endswith((".xlsx", ".xls")):
        wb = openpyxl.load_workbook(io.BytesIO(conteudo), data_only=True)
        linhas = []
        for nome_aba in wb.sheetnames:
            ws = wb[nome_aba]
            linhas.append(f"[Aba: {nome_aba}]")
            for row in ws.iter_rows(values_only=True):
                linha = "\t".join("" if c is None else str(c) for c in row)
                if linha.strip():
                    linhas.append(linha)
        return "\n".join(linhas)
    return conteudo.decode("utf-8", errors="replace")


# ── Histórico de análises ────────────────────────────────────────────────────
HISTORICO_FILE = Path("historico.json")

def _carregar_historico() -> list:
    try:
        if HISTORICO_FILE.exists():
            return json.loads(HISTORICO_FILE.read_text(encoding="utf-8"))
    except Exception:
        pass
    return []

_historico: list = _carregar_historico()

def _salvar_historico():
    try:
        HISTORICO_FILE.write_text(
            json.dumps(_historico, ensure_ascii=False, indent=2), encoding="utf-8"
        )
    except Exception:
        pass

_SEGMENTOS = [
    ("Saúde",                  ["saúde", "saude", "médic", "medic", "hospital", "medicament", "ubs", "enfermagem", "cirúrgic", "farmác", "farmac", "ambulatorial"]),
    ("Educação",               ["escola", "educação", "educacao", "pedagóg", "pedagogic", "didátic", "ensino", "aluno", "professor", "material escolar", "creche"]),
    ("Obras e Infraestrutura", ["obras", "construção", "construcao", "reforma", "paviment", "infraestrutura", "engenharia", "elétric", "eletric", "hidráulic", "hidraulic", "saneamento"]),
    ("Alimentação",            ["aliment", "merenda", "refeição", "refeicao", "gêneros alimentíc", "generos aliment", "nutri", "cozinha", "marmita"]),
    ("Tecnologia e TI",        ["software", "hardware", "computador", "informática", "informatica", "sistema", "licença", "servidor", " ti ", "tecnologia da informação", "impressora"]),
    ("Transporte",             ["veículo", "veiculo", "frota", "combustível", "combustivel", "ônibus", "onibus", "manutenção veicular", "locação de veículo", "locacao de veiculo"]),
    ("Viagens e Passagens",    ["passagem aérea", "passagem aerea", "passagem área", "bilhete aéreo", "bilhete aereo", "aéreo", "aereo", "aérea", "aerea", "aviação", "aviacao", "companhia aérea", "companhia aerea", "passagem", "hospedagem", "diária", "diaria", "hotel", "viagem"]),
    ("Eventos e Capacitação",  ["evento", "congresso", "capacitação", "capacitacao", "treinamento", "curso", "palestra", "cerimônia", "cerimonia"]),
    ("Limpeza e Conservação",  ["limpeza", "higien", "conservação predial", "conservacao predial", "jardinagem", "desinfeção", "desinfecao", "asseio", "zeladoria"]),
    ("Mobiliário e Escritório",["mobiliário", "mobiliario", "mobília", "mobilia", "escritório", "escritorio", "papel", "caneta", "grampe", "cadeira", "mesa", "material de escritório", "material de escritorio"]),
    ("Segurança",              ["segurança", "seguranca", "vigilância", "vigilancia", "monitoramento", "câmera", "camera", "cctv", "alarme", "portaria"]),
]

def detectar_segmento(texto: str) -> str:
    t = texto.lower()
    for nome, palavras in _SEGMENTOS:
        if any(p in t for p in palavras):
            return nome
    return "Outros"

def extrair_campo(ficha: str, campo: str) -> str:
    # padrão markdown: | **Campo** | valor |
    m = re.search(rf'\|\s*\*\*{re.escape(campo)}\*\*\s*\|\s*([^|\n]+)', ficha)
    if m:
        return m.group(1).strip()
    # padrão texto puro: "Campo: valor" ou "Campo    valor"
    m = re.search(rf'(?:^|\n)\s*{re.escape(campo)}\s*[:\t|]+\s*([^\n]+)', ficha, re.IGNORECASE)
    if m:
        return m.group(1).strip()[:150]
    return "Não informado"

def extrair_objeto(ficha: str) -> str:
    # seção markdown
    m = re.search(r'## Objeto\s*\n+(.+?)(?:\n##|\Z)', ficha, re.DOTALL)
    if m:
        return m.group(1).strip()[:200]
    # seção texto puro
    m = re.search(r'Objeto\s*\n+(.+?)(?:\n\n|\Z)', ficha, re.DOTALL)
    if m:
        return m.group(1).strip()[:200]
    return "Não informado"

def _eh_ficha(texto: str) -> bool:
    # normaliza espaços e coloca em maiúsculas
    t = " ".join(texto.upper().split())
    # match direto (com ou sem acento)
    if "FICHA DE LICITAÇ" in t or "FICHA DE LICITAC" in t:
        return True
    # "FICHA" + "LICITA" em qualquer lugar (cobre encoding quebrado)
    if "FICHA" in t and "LICITA" in t:
        return True
    # fallback: presença de vários campos típicos de ficha
    campos_tipicos = [
        "VALOR ESTIMADO", "DOCUMENTOS DE HABILITA", "ITENS A COTAR",
        "MODALIDADE", "VIGÊNCIA", "VIGENCIA", "CRITÉRIO", "CRITERIO",
        "PRAZO DE PAGAMENTO", "CONTATO DO", "ABERTURA",
    ]
    return sum(1 for c in campos_tipicos if c in t) >= 3

def registrar_analise(ficha: str):
    registro = {
        "id":        uuid.uuid4().hex[:10],
        "timestamp": datetime.datetime.now().isoformat(timespec="seconds"),
        "orgao":     extrair_campo(ficha, "Órgão"),
        "valor":     extrair_campo(ficha, "Valor Estimado Total"),
        "objeto":    extrair_objeto(ficha),
        "segmento":  detectar_segmento(ficha),
        "ficha":     ficha,
    }
    _historico.insert(0, registro)
    if len(_historico) > 500:
        _historico.pop()
    _salvar_historico()

def _reclassificar_historico():
    mudou = False
    for r in _historico:
        novo = detectar_segmento(r.get("ficha", r.get("objeto", "")))
        if r.get("segmento") != novo:
            r["segmento"] = novo
            mudou = True
    if mudou:
        _salvar_historico()

_reclassificar_historico()


MAX_CHARS = 400_000

# Textos pequenos: Groq e OpenRouter primeiro (gratuitos), OpenAI só se necessário
# Textos grandes: OpenAI primeiro (melhor qualidade para docs longos)
LIMITE_PEQUENO = 15_000  # chars — abaixo disso evita cobrar do OpenAI

PROVEDORES_PEQUENO = [
    (_groq,       "llama-3.1-8b-instant",                    18_000),
    (_groq2,      "llama-3.1-8b-instant",                    18_000),
    (_openrouter, "google/gemma-3-12b-it:free",              400_000),
    (_openrouter, "google/gemma-3-27b-it:free",              400_000),
    (_openrouter, "google/gemma-4-26b-a4b-it:free",          400_000),
    (_openrouter, "meta-llama/llama-3.3-70b-instruct:free",  400_000),
    (_openrouter, "nvidia/nemotron-3-super-120b-a12b:free",  400_000),
    (_openai,     "gpt-4.1-nano",                            400_000),
]

PROVEDORES_GRANDE = [
    (_openai,     "gpt-4.1-nano",                            400_000),
    (_openrouter, "google/gemma-3-12b-it:free",              400_000),
    (_openrouter, "google/gemma-3-27b-it:free",              400_000),
    (_openrouter, "google/gemma-4-26b-a4b-it:free",          400_000),
    (_openrouter, "meta-llama/llama-3.3-70b-instruct:free",  400_000),
    (_openrouter, "nvidia/nemotron-3-super-120b-a12b:free",  400_000),
    (_groq,       "llama-3.1-8b-instant",                    18_000),
    (_groq2,      "llama-3.1-8b-instant",                    18_000),
]


async def chamar_groq(texto: str, num_docs: int) -> str:
    ultimo_erro = ""
    provedores = PROVEDORES_PEQUENO if len(texto) <= LIMITE_PEQUENO else PROVEDORES_GRANDE

    for cliente, modelo, max_chars in provedores:
        texto_truncado = texto[:max_chars]
        user_prompt = USER_TEMPLATE.format(num_docs=num_docs, texto=texto_truncado)
        try:
            response = await cliente.chat.completions.create(
                model=modelo,
                max_tokens=8192,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt},
                ],
            )

            if not response.choices:
                ultimo_erro = f"Modelo {modelo} retornou resposta vazia"
                continue
            ficha = (response.choices[0].message.content or "").strip()
            idx = ficha.find("## FICHA")
            if idx > 0:
                ficha = ficha[idx:]
            if ficha.startswith("## FICHA"):
                _stats["total_analises"] += 1
                uso = getattr(response, "usage", None)
                tok_in  = getattr(uso, "prompt_tokens", 0) or 0
                tok_out = getattr(uso, "completion_tokens", 0) or 0
                ci, co  = _CUSTO.get(modelo, (0.0, 0.0))
                custo   = (tok_in * ci + tok_out * co) / 1_000_000
                _stats["tokens_input_total"]  += tok_in
                _stats["tokens_output_total"] += tok_out
                _stats["custo_usd_total"]     += custo
                p = _stats["por_provedor"].setdefault(modelo, {"analises": 0, "tokens": 0, "custo_usd": 0.0})
                p["analises"] += 1
                p["tokens"]   += tok_in + tok_out
                p["custo_usd"] = round(p["custo_usd"] + custo, 6)
                return ficha
            ultimo_erro = f"Modelo {modelo} não seguiu o formato esperado"
            continue
        except openai.APITimeoutError:
            raise HTTPException(504, "Tempo limite excedido ao chamar a API.")
        except openai.APIConnectionError:
            raise HTTPException(500, "Erro de conexão com a API.")
        except openai.APIStatusError as e:
            if e.status_code in (400, 401, 402, 404, 413, 429, 503):
                msg = str(e.message)
                # extrai tempo de retry da mensagem da API
                m = re.search(r'retry in (\d+(?:\.\d+)?)\s*s', msg, re.IGNORECASE)
                if m:
                    segundos = int(float(m.group(1))) + 1
                    if segundos >= 3600:
                        tempo = f"{segundos // 3600}h"
                    elif segundos >= 60:
                        tempo = f"{segundos // 60} minutos"
                    else:
                        tempo = f"{segundos} segundos"
                    ultimo_erro = tempo
                elif 'per-day' in msg or 'per_day' in msg or 'daily' in msg.lower():
                    ultimo_erro = "algumas horas (limite diário atingido)"
                else:
                    ultimo_erro = "alguns minutos"
                continue
            raise HTTPException(500, f"Erro ao chamar a API: {e.message}")

    raise HTTPException(503, f"Todas as IAs estão sobrecarregadas no momento. Tente novamente em {ultimo_erro or 'alguns minutos'}.")


@app.get("/status", response_class=HTMLResponse)
async def status():
    total   = _stats["total_analises"]
    custo   = _stats["custo_usd_total"]
    hoje    = _stats["analises_hoje"]
    rest    = max(0, LIMITE_DIARIO - hoje)
    pct     = round(hoje / LIMITE_DIARIO * 100)
    bar_cor = "#2e7d32" if pct < 70 else "#f57c00" if pct < 90 else "#c62828"
    c_medio = custo / total if total else 0
    hist_n  = len(_historico)

    # segmentos do histórico
    seg_count: dict = {}
    for r in _historico:
        s = r.get("segmento", "Outros")
        seg_count[s] = seg_count.get(s, 0) + 1
    seg_rows = "".join(
        f'<div class="seg-row"><span>{s}</span><span class="seg-n">{n}</span></div>'
        for s, n in sorted(seg_count.items(), key=lambda x: -x[1])
    ) or '<p style="color:#bbb;font-size:.85rem;text-align:center;padding:16px 0">Nenhum histórico ainda</p>'

    # linhas de provedores
    def _tag(m: str) -> str:
        return '<span class="tag-free">gratuito</span>' if (":free" in m or "instant" in m) else '<span class="tag-pago">pago</span>'

    prov_rows = "".join(
        f"<tr><td>{m}<br><small>{_tag(m)}</small></td>"
        f"<td style='text-align:center'>{p['analises']}</td>"
        f"<td style='text-align:center'>{p['tokens']:,}</td>"
        f"<td>US$ {p['custo_usd']:.5f}</td></tr>"
        for m, p in _stats["por_provedor"].items()
    ) or '<tr><td colspan="4" style="color:#bbb;text-align:center;padding:18px">Nenhuma análise nesta sessão</td></tr>'

    tok_in  = _stats["tokens_input_total"]
    tok_out = _stats["tokens_output_total"]
    data_reset = _stats["hoje"]

    return f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Status — LicitaPro</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
<style>
:root{{
  --brand-900:#061A33;--brand-800:#0A2540;--brand-600:#1E4FA0;--brand-500:#2F6FE0;
  --brand-100:#E6EEFC;--brand-50:#F4F8FE;
  --ink-900:#111827;--ink-800:#1F2937;--ink-600:#4B5563;--ink-500:#6B7280;
  --ink-400:#9CA3AF;--ink-300:#D1D5DB;--ink-200:#E5E7EB;--ink-150:#EEF0F3;
  --ink-100:#F3F4F6;--ink-50:#F9FAFB;--ink-0:#FFFFFF;
  --success-700:#166534;--success-100:#DCFCE7;
  --warn-700:#92400E;--warn-500:#F59E0B;--warn-50:#FFFBEB;
  --danger-700:#991B1B;--danger-500:#EF4444;--danger-50:#FEF2F2;
  --bg:#FFFFFF;--bg-subtle:#FAFBFC;--surface:var(--ink-0);
  --fg-1:var(--ink-900);--fg-2:var(--ink-600);--fg-3:var(--ink-500);--fg-4:var(--ink-400);
  --border:var(--ink-200);--border-subtle:var(--ink-150);
  --font-sans:'Inter',-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;
  --font-mono:'JetBrains Mono',Menlo,Consolas,monospace;
  --radius-sm:6px;--radius-md:10px;--radius-lg:14px;--radius-full:9999px;
  --shadow-sm:0 1px 2px rgba(11,15,20,.04),0 1px 3px rgba(11,15,20,.06);
  --ease-out:cubic-bezier(0.22,1,0.36,1);
}}
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:var(--font-sans);background:var(--bg-subtle);color:var(--fg-1);min-height:100vh;-webkit-font-smoothing:antialiased}}

nav{{position:sticky;top:0;z-index:10;background:rgba(255,255,255,.72);backdrop-filter:blur(20px) saturate(180%);-webkit-backdrop-filter:blur(20px) saturate(180%);border-bottom:1px solid var(--border-subtle)}}
.nav-inner{{max-width:960px;margin:0 auto;padding:0 24px;height:56px;display:flex;align-items:center;justify-content:space-between;gap:16px}}
.logo{{font-size:17px;font-weight:700;color:var(--ink-900);letter-spacing:-.025em}}
.logo-dot{{color:var(--brand-500)}}
.btn-back{{display:inline-flex;align-items:center;gap:6px;padding:7px 13px;border-radius:var(--radius-md);border:1px solid var(--border);background:transparent;color:var(--fg-2);font-size:13px;font-weight:500;font-family:var(--font-sans);cursor:pointer;text-decoration:none;transition:background .12s}}
.btn-back:hover{{background:var(--ink-50);color:var(--fg-1)}}

main{{max-width:960px;margin:0 auto;padding:32px 24px 64px}}
.page-header{{margin-bottom:28px}}
.page-title{{font-size:22px;font-weight:600;color:var(--ink-900);letter-spacing:-.025em}}
.page-sub{{font-size:13px;color:var(--fg-3);margin-top:4px;font-variant-numeric:tabular-nums}}

.grid{{display:grid;gap:14px;margin-bottom:14px}}
.g4{{grid-template-columns:repeat(4,1fr)}}
.g3{{grid-template-columns:repeat(3,1fr)}}
.g2{{grid-template-columns:1fr 1fr}}
@media(max-width:720px){{.g4,.g3{{grid-template-columns:1fr 1fr}}}}
@media(max-width:460px){{.g4,.g3,.g2{{grid-template-columns:1fr}}}}

.card{{background:var(--surface);border:1px solid var(--border);border-radius:var(--radius-lg);padding:20px 22px;box-shadow:var(--shadow-sm)}}
.stat-label{{font-size:11px;font-weight:600;letter-spacing:.06em;text-transform:uppercase;color:var(--fg-3);margin-bottom:8px}}
.stat-val{{font-size:32px;font-weight:700;color:var(--ink-900);line-height:1;letter-spacing:-.025em;font-variant-numeric:tabular-nums}}
.stat-val-sm{{font-size:24px;font-weight:700;color:var(--ink-900);line-height:1;letter-spacing:-.015em;font-variant-numeric:tabular-nums}}
.stat-sub{{font-size:12px;color:var(--fg-4);margin-top:5px;font-variant-numeric:tabular-nums}}
.stat-suffix{{font-size:17px;color:var(--fg-3);font-weight:500}}

.bar-wrap{{background:var(--ink-150);border-radius:var(--radius-full);height:6px;margin-top:14px;overflow:hidden}}
.bar{{height:100%;border-radius:var(--radius-full);transition:width .4s var(--ease-out)}}

.sec-title{{font-size:12px;font-weight:600;letter-spacing:.06em;text-transform:uppercase;color:var(--fg-3);margin-bottom:14px;padding-bottom:10px;border-bottom:1px solid var(--border-subtle)}}

table{{width:100%;border-collapse:collapse;font-size:13px}}
th{{padding:9px 12px;text-align:left;border-bottom:1px solid var(--border);background:var(--ink-50);font-weight:600;font-size:11px;text-transform:uppercase;letter-spacing:.06em;color:var(--fg-3)}}
td{{padding:9px 12px;text-align:left;border-bottom:1px solid var(--border-subtle);vertical-align:middle;color:var(--fg-1);font-variant-numeric:tabular-nums}}
tr:last-child td{{border-bottom:none}}
tr:hover td{{background:var(--ink-50)}}

.seg-row{{display:flex;justify-content:space-between;align-items:center;padding:9px 0;border-bottom:1px solid var(--border-subtle);font-size:13px;color:var(--fg-2)}}
.seg-row:last-child{{border-bottom:none}}
.seg-n{{font-weight:600;color:var(--brand-600);background:var(--brand-50);padding:2px 10px;border-radius:var(--radius-full);font-size:12px;font-variant-numeric:tabular-nums}}

.tag-free{{background:var(--success-100);color:var(--success-700);font-size:11px;padding:2px 8px;border-radius:var(--radius-full);font-weight:600}}
.tag-pago{{background:var(--warn-50);color:var(--warn-700);font-size:11px;padding:2px 8px;border-radius:var(--radius-full);font-weight:600}}

.footer-note{{text-align:right;font-size:12px;color:var(--fg-4);margin-top:12px;font-variant-numeric:tabular-nums}}
</style>
</head>
<body>
<nav>
  <div class="nav-inner">
    <span class="logo">Licita<span class="logo-dot">Pro</span></span>
    <a class="btn-back" href="/">
      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m15 18-6-6 6-6"/></svg>
      Voltar
    </a>
  </div>
</nav>
<main>
  <div class="page-header">
    <h1 class="page-title">Status do sistema</h1>
    <p class="page-sub">Sessão atual &nbsp;·&nbsp; Reseta em: {data_reset}</p>
  </div>

  <div class="grid g4">
    <div class="card">
      <div class="stat-label">Análises hoje</div>
      <div class="stat-val">{hoje}<span class="stat-suffix"> / {LIMITE_DIARIO}</span></div>
      <div class="bar-wrap"><div class="bar" style="width:{pct}%;background:{bar_cor}"></div></div>
      <div class="stat-sub">{pct}% do limite diário</div>
    </div>
    <div class="card">
      <div class="stat-label">Restantes hoje</div>
      <div class="stat-val" style="color:{bar_cor}">{rest}</div>
      <div class="stat-sub">análises disponíveis</div>
    </div>
    <div class="card">
      <div class="stat-label">Total na sessão</div>
      <div class="stat-val">{total}</div>
      <div class="stat-sub">análises realizadas</div>
    </div>
    <div class="card">
      <div class="stat-label">Histórico salvo</div>
      <div class="stat-val">{hist_n}</div>
      <div class="stat-sub">análises no arquivo</div>
    </div>
  </div>

  <div class="grid g3">
    <div class="card">
      <div class="stat-label">Custo total (sessão)</div>
      <div class="stat-val-sm">US$ {custo:.4f}</div>
      <div class="stat-sub">R$ {custo * 5.75:.2f} · câmbio 5,75</div>
    </div>
    <div class="card">
      <div class="stat-label">Custo médio / análise</div>
      <div class="stat-val-sm">US$ {c_medio:.4f}</div>
      <div class="stat-sub">R$ {c_medio * 5.75:.4f}</div>
    </div>
    <div class="card">
      <div class="stat-label">Tokens consumidos</div>
      <div class="stat-val-sm">{tok_in + tok_out:,}</div>
      <div class="stat-sub">{tok_in:,} entrada &nbsp;·&nbsp; {tok_out:,} saída</div>
    </div>
  </div>

  <div class="grid g2">
    <div class="card">
      <div class="sec-title">Por provedor — sessão atual</div>
      <table>
        <thead><tr><th>Modelo</th><th style="text-align:center">Análises</th><th style="text-align:right">Tokens</th><th style="text-align:right">Custo</th></tr></thead>
        <tbody>{prov_rows}</tbody>
      </table>
    </div>
    <div class="card">
      <div class="sec-title">Histórico por segmento</div>
      {seg_rows}
    </div>
  </div>

  <p class="footer-note">Atualiza automaticamente a cada 30 s &nbsp;·&nbsp; {_stats["hoje"]}</p>
</main>
<script>setTimeout(()=>location.reload(),30000);</script>
</body>
</html>"""


@app.post("/importar/arquivo")
async def importar_arquivo(arquivos: list[UploadFile] = File(...)):
    if not arquivos:
        raise HTTPException(400, "Nenhum arquivo enviado.")
    importados, ignorados = [], []
    for arq in arquivos:
        conteudo = await arq.read()
        try:
            texto = extrair_texto(arq.filename, conteudo)
        except Exception as e:
            ignorados.append({"arquivo": arq.filename, "motivo": f"erro ao ler: {e}"})
            continue
        texto = (texto or "").strip()
        if not texto:
            ignorados.append({"arquivo": arq.filename, "motivo": "nenhum texto extraído do arquivo"})
            continue
        # já em markdown → usa direto; texto puro → envolve com cabeçalho
        if "## FICHA" in texto:
            ficha = texto[texto.find("## FICHA"):]
        else:
            ficha = "## FICHA DE LICITAÇÃO\n\n" + texto
        registrar_analise(ficha)
        importados.append(arq.filename)
    return {"importados": importados, "ignorados": ignorados}


@app.post("/importar/texto")
async def importar_texto(request: AnalisarRequest):
    texto = request.texto.strip()
    if not texto:
        raise HTTPException(400, "Texto vazio.")
    ficha = texto[texto.find("## FICHA"):] if "## FICHA" in texto else "## FICHA DE LICITAÇÃO\n\n" + texto
    registrar_analise(ficha)
    return {"ok": True}


@app.post("/api/reclassificar")
async def api_reclassificar():
    antes = {r["id"]: r.get("segmento") for r in _historico}
    _reclassificar_historico()
    atualizados = sum(1 for r in _historico if antes.get(r["id"]) != r.get("segmento"))
    return {"atualizados": atualizados, "total": len(_historico)}


@app.get("/historico")
async def get_historico():
    return {"historico": [{k: v for k, v in r.items() if k != "ficha"} for r in _historico]}

@app.get("/historico/{id}")
async def get_ficha_historico(id: str):
    for r in _historico:
        if r["id"] == id:
            return {"ficha": r["ficha"], "orgao": r["orgao"], "segmento": r["segmento"]}
    raise HTTPException(404, "Análise não encontrada.")


@app.get("/", response_class=HTMLResponse)
async def root():
    return HTML_PAGE


@app.post("/analisar/arquivo", response_model=AnalisarResponse)
async def analisar_arquivo(arquivos: list[UploadFile] = File(...)):
    if not arquivos:
        raise HTTPException(400, "Nenhum arquivo enviado.")

    # reset diário
    hoje = datetime.date.today().isoformat()
    if _stats["hoje"] != hoje:
        _stats["hoje"] = hoje
        _stats["analises_hoje"] = 0

    if _stats["analises_hoje"] >= LIMITE_DIARIO:
        raise HTTPException(429, f"Limite diário de {LIMITE_DIARIO} análises atingido. Tente novamente amanhã.")

    textos = []
    for arq in arquivos:
        conteudo = await arq.read()
        try:
            texto = extrair_texto(arq.filename, conteudo)
        except Exception as e:
            raise HTTPException(400, f"Erro ao ler '{arq.filename}': {e}")
        textos.append((arq.filename, texto))

    cota = MAX_CHARS // len(textos)
    partes = []
    for nome, txt in textos:
        if len(txt) <= cota:
            trecho = txt
        else:
            # pega 60% do início (cabeçalho, objeto, datas, valor)
            # e 40% do fim (itens, documentos, alertas)
            inicio = int(cota * 0.60)
            fim    = cota - inicio
            trecho = txt[:inicio] + "\n\n[...]\n\n" + txt[-fim:]
        partes.append(f"=== {nome} ===\n{trecho}")
    texto_completo = "\n\n".join(partes)
    ficha = await chamar_groq(texto_completo, len(arquivos))
    _stats["analises_hoje"] += 1
    registrar_analise(ficha)
    return AnalisarResponse(ficha=ficha)


@app.post("/analisar", response_model=AnalisarResponse)
async def analisar(request: AnalisarRequest):
    ficha = await chamar_groq(request.texto, request.num_docs)
    registrar_analise(ficha)
    return AnalisarResponse(ficha=ficha)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
