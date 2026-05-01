# LicitaPRO - Proposta de analise sem API de IA

Data: 2026-05-01

## Decisao tecnica

Implementar parser deterministico local como primeira tentativa, mantendo OpenAI/Groq/OpenRouter como fallback quando a confianca for baixa.

Nao e recomendavel substituir a IA 100% neste momento. Editais brasileiros seguem padroes, mas variam bastante em PDF, numeracao, tabelas, anexos e secoes de habilitacao. O modo hibrido reduz custo sem degradar a qualidade do resultado.

## O que fica local

- Numero do edital ou processo
- Orgao comprador
- CNPJ
- Modalidade
- Objeto
- Valor estimado
- Data de abertura
- Prazo de envio de proposta
- Prazo de vigencia
- Criterio de julgamento
- Documentos de habilitacao mais comuns
- Segmento

## O que continua melhor com IA

- Analise juridica de risco
- Resumo executivo narrativo
- Comparacao entre editais
- Interpretacao de editais mal formatados
- PDFs escaneados sem texto extraivel
- Itens a cotar quando estao em tabelas complexas ou anexos extensos

## Arquitetura implementada

Fluxo atual:

```text
upload -> extracao de texto -> IA -> ficha markdown -> historico
```

Fluxo hibrido:

```text
upload -> extracao de texto -> parser_edital.analisar_sem_api()
                                  |
                                  +-- confianca >= limite -> ficha local
                                  |
                                  +-- confianca < limite -> fallback IA
```

Variaveis de ambiente:

```env
USAR_PARSER_LOCAL=true
PARSER_FALLBACK_API=true
PARSER_MIN_CONFIANCA=70
```

## Criterio de confianca

O parser pontua campos extraidos por peso:

- Objeto, numero, orgao, valor e data de abertura pesam mais.
- CNPJ, modalidade, vigencia, criterio e habilitacao complementam a confianca.
- Abaixo de `PARSER_MIN_CONFIANCA`, a aplicacao chama a IA se `PARSER_FALLBACK_API=true`.

## Como testar

Teste unitario sintetico:

```bash
python -m unittest discover -s tests
```

Teste real:

1. Separar 10 editais reais com segmentos diferentes.
2. Enviar pelo ambiente `dev`.
3. Registrar para cada edital:
   - se usou parser local ou fallback IA;
   - confianca;
   - campos incorretos;
   - campos nao identificados;
   - tempo de resposta.
4. Ajustar regex somente com falhas recorrentes.

## Criterio para desligar API

So considerar `PARSER_FALLBACK_API=false` depois que o parser acertar campos essenciais em pelo menos 8 de 10 editais reais:

- numero/processo;
- orgao;
- modalidade;
- objeto;
- valor ou data de abertura.
