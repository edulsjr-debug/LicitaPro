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

## Parser local sem API

O LicitaPRO pode tentar extrair campos do edital localmente antes de chamar provedores de IA. Esse modo reduz custo e dependencia externa, mas mantem a API como fallback quando a confianca do parser for baixa.

Variaveis:

```env
USAR_PARSER_LOCAL=true
PARSER_FALLBACK_API=true
PARSER_MIN_CONFIANCA=70
```

Com `PARSER_FALLBACK_API=true`, o fluxo e:

```text
parser local com confianca suficiente -> salva ficha sem custo de API
parser local com baixa confianca      -> chama OpenAI/Groq/OpenRouter
```

Detalhes: [`PROPOSTA_SEM_API.md`](PROPOSTA_SEM_API.md)

---

## OCR no upload

Quando um PDF vem escaneado ou com pouco texto extraível, o upload tenta OCR automaticamente antes de salvar o texto para análise.

Variaveis:

```env
OCR_HABILITADO=true
OCR_MIN_CHAR=120
OCR_MAX_PAGINAS=20
OCR_DPI=220
```

O fluxo e:

```text
PDF -> texto nativo -> OCR por pagina se o texto vier fraco -> analise
```

O OCR e aplicado no proprio processo de upload, sem etapa manual.

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
GEMINI_API_KEY=sua_chave
OPENROUTER_API_KEY=sua_chave
GROQ_API_KEY=sua_chave
GROQ_API_KEY2=sua_chave
PARSER_MAX_CHARS_FALLBACK=80000
```

Inicie o servidor:

```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

Acesse: **http://localhost:8000**

---

## Ambientes

| Ambiente | URL | Branch |
|---|---|---|
| Produção | https://licitapro-0brh.onrender.com | `master` |
| Teste | https://licitapro-dev.onrender.com | `dev` |

Ambos monitorados pelo **UptimeRobot** a cada 5 minutos para evitar hibernação do plano gratuito do Render.

---

## Banco de dados (Supabase)

O histórico de análises é persistido no **Supabase PostgreSQL** — não se perde em redeploys.

- Tabela: `historico` (campo `id` TEXT PRIMARY KEY, `dados` JSONB)
- Na primeira inicialização com `DATABASE_URL` configurada, o sistema migra automaticamente o `historico.json` local para o banco
- Sem `DATABASE_URL`, funciona em modo local com `historico.json` como fallback

Variável de ambiente necessária:
```
DATABASE_URL=postgresql://postgres:[SENHA]@db.[PROJETO].supabase.co:5432/postgres?sslmode=require
```

---

## Fluxo de desenvolvimento

```
dev branch  →  testa em licitapro-dev.onrender.com
    ↓  (validado)
master branch  →  deploy automático em licitapro-0brh.onrender.com
```

Nunca subir alterações direto no `master` sem testar no `dev` antes.

---

## Deploy (Render)

O repositório já inclui `render.yaml` configurado.

**Variáveis de ambiente obrigatórias:**

| Variável | Descrição |
|---|---|
| `OPENAI_API_KEY` | Chave da OpenAI |
| `GEMINI_API_KEY` | Chave do Google Gemini (AI Studio) |
| `OPENROUTER_API_KEY` | Chave do OpenRouter |
| `GROQ_API_KEY` | Chave do Groq (conta 1) |
| `GROQ_API_KEY2` | Chave do Groq (conta 2) |
| `PARSER_MAX_CHARS_FALLBACK` | Tamanho máximo do texto para permitir fallback por API |
| `DATABASE_URL` | Connection string do Supabase (PostgreSQL) |

**Passos para novo ambiente:**
1. Acesse [render.com](https://render.com) → **New → Web Service**
2. Conecte o repositório `edulsjr-debug/LicitaPro`
3. Selecione o branch desejado (`master` para produção, `dev` para teste)
4. Preencha as 5 variáveis de ambiente acima
5. Clique em **Deploy**
6. Adicione monitor no [UptimeRobot](https://uptimerobot.com) para manter o serviço ativo

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
