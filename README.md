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
| `OPENROUTER_API_KEY` | Chave do OpenRouter |
| `GROQ_API_KEY` | Chave do Groq (conta 1) |
| `GROQ_API_KEY2` | Chave do Groq (conta 2) |
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
