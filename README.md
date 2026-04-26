# LicitaPro

Sistema web de análise de editais de licitação com IA. Processa PDFs e documentos de editais públicos, extrai os pontos críticos automaticamente e gera uma **Ficha de Licitação** estruturada — economizando horas de leitura jurídica.

---

## Funcionalidades

### Análise de editais
- Upload de arquivos por **drag & drop** ou clique
- Suporte a **PDF, DOCX, XLSX, XLS, TXT**
- Envio de **múltiplos arquivos** ao mesmo tempo (edital + anexos)
- Geração automática da Ficha de Licitação via IA

### Ficha de Licitação gerada
| Campo | Descrição |
|---|---|
| Nº e Processo | Número do edital e processo administrativo |
| Órgão contratante | Nome e contato do órgão |
| Modalidade e Critério | Pregão, Concorrência, etc. |
| Valor Estimado | Valor total estimado do contrato |
| Vigência do contrato | Prazo de duração |
| Datas | Abertura da sessão e limite para proposta |
| Garantia e Pagamento | Percentual de garantia e prazo de pagamento |
| Patrimônio / Capital mínimo | Exigências financeiras de habilitação |
| Itens a cotar | Tabela com descrição, quantidade e valores |
| Documentos de habilitação | Lista organizada por categoria |
| Alertas | Pontos críticos e cláusulas de atenção |

### Histórico
- Todas as análises são **salvas automaticamente**
- Painel lateral com busca por órgão ou objeto
- Filtro por **segmento** (Saúde, Educação, Viagens, etc.)
- Segmentos detectados automaticamente pela IA
- Exportação individual como PDF (via impressão do navegador)

### Importação de fichas prontas
- Import de fichas já realizadas via arquivo (PDF, DOCX, TXT)
- Import via texto colado diretamente na interface

### Página de status (`/status`)
- Análises realizadas no dia e limite diário (20/dia)
- Custo total e custo médio por análise (USD e BRL)
- Tokens consumidos (entrada e saída)
- Breakdown por provedor de IA
- Histórico por segmento

---

## Provedores de IA

O sistema usa múltiplos provedores com fallback automático:

| Provedor | Modelo | Tipo |
|---|---|---|
| OpenAI | gpt-4.1-nano / gpt-4o-mini | Pago |
| OpenRouter | Gemma, Llama, Nemotron | Gratuito |
| Groq | llama-3.3-70b-versatile | Gratuito |

- Editais pequenos (até ~15 mil caracteres) → provedores **gratuitos**
- Editais grandes → **OpenAI** como prioridade (melhor qualidade)
- Se todos os provedores estiverem ocupados, o sistema informa o tempo de espera

---

## Instalação local

**Pré-requisitos:** Python 3.9+

```bash
git clone https://github.com/edulsjr-debug/LicitaPro.git
cd LicitaPro

python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Linux / macOS

pip install -r requirements.txt
```

Crie o arquivo `.env` na raiz do projeto:

```
OPENAI_API_KEY=sua_chave
OPENROUTER_API_KEY=sua_chave
GROQ_API_KEY=sua_chave
GROQ_API_KEY2=sua_chave
```

Inicie o servidor:

```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

Acesse: **http://localhost:8000**

---

## Deploy (Render)

O repositório já inclui `render.yaml` configurado.

1. Acesse [render.com](https://render.com) e crie um **Web Service**
2. Conecte o repositório `edulsjr-debug/LicitaPro`
3. Preencha as variáveis de ambiente (`OPENAI_API_KEY`, etc.)
4. Clique em **Deploy**

> **Atenção:** no plano gratuito do Render o histórico de análises é perdido ao reiniciar o serviço. Para histórico persistente é necessário configurar um banco de dados.

---

## Endpoints da API

| Método | Rota | Descrição |
|---|---|---|
| GET | `/` | Interface principal |
| GET | `/status` | Painel de uso e custos |
| POST | `/analisar/arquivo` | Analisa arquivos enviados |
| POST | `/analisar` | Analisa texto direto (JSON) |
| GET | `/historico` | Lista todo o histórico |
| GET | `/historico/{id}` | Retorna ficha de uma análise |
| POST | `/importar/arquivo` | Importa fichas prontas via arquivo |
| POST | `/importar/texto` | Importa ficha via texto colado |
| POST | `/api/reclassificar` | Reclassifica segmentos do histórico |

---

## Stack

- **Backend:** FastAPI + Uvicorn
- **IA:** OpenAI SDK (compatível com OpenRouter e Groq)
- **Extração de documentos:** pdfplumber, python-docx, openpyxl
- **Frontend:** HTML/CSS/JS vanilla com design system LicitaPro
- **Fontes:** Inter + JetBrains Mono (Google Fonts)
