# Releases

## v2026.05.01
- Parser local mais preciso para número, órgão, valor e data.
- OCR automático no upload de PDFs escaneados.
- Fallback por API evitado em documentos longos para reduzir timeout.

## v2026.05.02
- Suite de medição do parser por pasta (`tests/run_fixtures.py`) com relatório em Markdown e PDFs por caso.
- Ajustes de robustez no parser (números maiores no n° do edital/processo, normalização de espaços no cabeçalho, fallback simples para modalidade).
- Fallback local opcional via LLM (Ollama) antes de gastar API externa.
- `historico.json` removido do repositório para não "voltar" histórico antigo a cada deploy.

