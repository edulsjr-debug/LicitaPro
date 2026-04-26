# Proxy Licitação

Servidor proxy local em FastAPI que analisa editais de licitação e gera uma Ficha de Licitação estruturada via API da Anthropic.

## Requisitos

- Python 3.9+
- Chave de API da Anthropic

## Instalação

```bash
cd C:\projetos\proxy-licitacao

# Criar e ativar ambiente virtual (recomendado)
python -m venv venv
venv\Scripts\activate       # Windows
# source venv/bin/activate  # Linux / macOS

# Instalar dependências
pip install -r requirements.txt
```

## Configuração

```bash
# Copie o arquivo de exemplo e edite com sua chave
copy .env.example .env
```

Abra o `.env` e substitua o valor:

```
ANTHROPIC_API_KEY=sk-ant-api03-SUA_CHAVE_AQUI
```

## Execução

```bash
python main.py
```

O servidor sobe em `http://localhost:8000`.

## Uso

### Endpoint

`POST /http://localhost:8000/analisar`

### Body (JSON)

```json
{
  "texto": "Cole aqui o texto completo do edital ou documento de licitação...",
  "num_docs": 2
}
```

| Campo     | Tipo   | Descrição                                 |
|-----------|--------|-------------------------------------------|
| `texto`   | string | Texto do edital a ser analisado           |
| `num_docs`| int    | Quantidade de documentos (padrão: `2`)    |

### Resposta

```json
{
  "ficha": "## FICHA DE LICITAÇÃO\n\n**Nº:** ..."
}
```

O campo `ficha` contém o Markdown estruturado com todos os campos da licitação.

### Exemplo com curl

```bash
curl -X POST http://localhost:8000/analisar \
  -H "Content-Type: application/json" \
  -d "{\"texto\": \"Pregão Eletrônico nº 001/2025...\", \"num_docs\": 1}"
```

## Campos gerados na Ficha

- Nº / Órgão / Processo / Objeto
- Valor Estimado / Modalidade / Critério
- Vigência / Garantia / Prazo de Pagamento
- Contato do Órgão / Prazos
- Modelo de Proposta (tipo de taxa, o que é cotado, como lançar, observação)
- Itens a Cotar com quantidades e valores
- Documentos de Habilitação organizados por categoria
- Alertas com pontos críticos

## Documentação interativa

Acesse `http://localhost:8000/docs` para a interface Swagger gerada automaticamente.
