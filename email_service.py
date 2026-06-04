import html as _html_mod
import os
import resend

_FROM = "LicitaPRO <noreply@prumosaas.com.br>"
_BASE_URL = "https://licitapro.prumosaas.com.br"


def send_analysis_complete(filename: str, score: int, analise_id: str) -> None:
    """Envia notificação de análise concluída para NOTIFY_EMAIL. Silencioso em falhas."""
    api_key = os.getenv("RESEND_API_KEY", "")
    notify_email = os.getenv("NOTIFY_EMAIL", "")
    if not api_key or not notify_email:
        return

    resend.api_key = api_key
    try:
        resend.Emails.send({
            "from": _FROM,
            "to": [notify_email],
            "subject": f"[LicitaPRO] Análise pronta — Score: {score}",
            "html": _html(filename, score, analise_id),
        })
    except Exception:
        pass  # nunca bloquear o pipeline de análise


def _html(filename: str, score: int, analise_id: str) -> str:
    score_color = "#22c55e" if score >= 70 else "#f59e0b" if score >= 40 else "#ef4444"
    url = f"{_BASE_URL}/historico/{analise_id}"
    safe_filename = _html_mod.escape(filename)
    return f"""<!DOCTYPE html>
<html lang="pt-BR">
<head><meta charset="UTF-8"><style>
body{{font-family:Inter,sans-serif;background:#fff;color:#0D0D0D;margin:0;padding:0}}
.c{{max-width:520px;margin:0 auto;padding:48px 32px}}
.logo{{font-size:11px;font-weight:600;letter-spacing:.2em;color:#B8924F;margin-bottom:40px}}
h1{{font-size:22px;font-weight:400;letter-spacing:-.02em;margin-bottom:8px}}
.fn{{font-size:12px;color:#888;margin-bottom:32px;font-family:monospace}}
.score{{font-size:52px;font-weight:600;color:{score_color};letter-spacing:-.03em;margin-bottom:4px;line-height:1}}
.sl{{font-size:11px;color:#888;letter-spacing:.12em;text-transform:uppercase;margin-bottom:32px}}
.btn{{display:inline-block;margin-top:8px;padding:12px 24px;background:#0D0D0D;color:#F5F2EC;text-decoration:none;font-size:12px;letter-spacing:.08em;font-weight:500}}
.ft{{margin-top:48px;padding-top:24px;border-top:1px solid #eee;font-size:11px;color:#999}}
a.gold{{color:#B8924F;text-decoration:none}}
</style></head>
<body>
  <div class="c">
    <div class="logo">| LICITAPRO</div>
    <h1>Análise concluída.</h1>
    <div class="fn">{safe_filename}</div>
    <div class="score">{score}</div>
    <div class="sl">Score de viabilidade</div>
    <a href="{url}" class="btn">→ Ver análise completa</a>
    <div class="ft">
      licitapro.prumosaas.com.br &nbsp;·&nbsp;
      <a href="https://prumosaas.com.br" class="gold">Prumo Software</a>
    </div>
  </div>
</body>
</html>"""
