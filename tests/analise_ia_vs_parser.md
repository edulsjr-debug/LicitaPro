# Analise "IA" vs Parser (Auditoria de Divergencias)

Data: 2026-05-02

Objetivo: olhar os casos que estao "falhando" no gabarito e separar:

1. Parser realmente errou (regex/logica).
2. Gabarito/fixture esta errado ou desatualizado.

Importante: aqui "IA" significa uma leitura humana/LLM-like do **texto real extraido** dos arquivos (sem chamar API externa).

## Resumo

Hoje, as falhas vistas em `tests/relatorio_precisao.md` sao **do gabarito** (fixture), nao do parser.

- `poco_verde`: o `valor` esperado (`14.133`) bate com **Lei 14.133/2021**, nao com o valor estimado do edital/termo de referencia.
- `trt7_passagens`: o `data_abertura` esperado (`04/05/2026`) **nao aparece** em nenhum arquivo da pasta `editais/4`. O unico carimbo de data encontrado no conjunto e `09/04/2026` (na "Relacao de Itens").

## Caso: `poco_verde` (editais/2)

### Divergencia

- Gabarito (fixture): `valor` contem `14.133`
- Parser extraiu: `R$ 360.604,58`

### Evidencia (texto real)

No arquivo `TERMO_DE_REFERENCIA___Viagens.pdf` (pasta `editais/2`), existe trecho explicitando o valor maximo estimado:

> "o valor maximo estimado da contratacao sera de **R$ 360.604,58** (...)".

E a sequencia `14.133` aparece como referencia a lei:

> "Lei 14.133/2021"

Conclusao: **o parser esta coerente**. O gabarito esta mirando o numero da lei, nao o valor do processo.

### Sugestao de correcoes no fixture

1. Trocar `esperado.valor` para conter `360.604` (ou `360.604,58`).
2. O range de `score` (hoje `max: 45`) parece desatualizado, ja que o parser entregou `55` com confianca alta. Ou ajusta o range, ou remove validacao de score enquanto o modelo de score estiver mudando.

## Caso: `trt7_passagens` (editais/4)

### Divergencia

- Gabarito (fixture): `data_abertura` contem `04/05/2026`
- Parser extraiu: `09/04/2026`

### Evidencia (texto real)

No arquivo `RelacaoItens08000405900092026000.pdf` (pasta `editais/4`), o texto contem:

> "PREGAO ELETRONICO No 90009/2026-000 ... **09/04/2026 15:17** (1/1)"

Ao varrer os demais arquivos da pasta `editais/4` (DOCX/ODT/PDF), **nao existe** a string `04/05/2026` nem outra data no formato `dd/mm/aaaa`. O `Edital.docx` traz a frase "na data, horario e local indicados neste Edital" sem informar uma data concreta.

Conclusao: do jeito que os arquivos estao hoje, **nao da para exigir `04/05/2026`** no gabarito; o check esta errado/inviavel.

### Sugestao de correcoes no fixture

1. Trocar `esperado.data_abertura` para conter `09/04/2026` (se o objetivo for validar "uma data encontrada no pacote").
2. Alternativa melhor: remover a validacao de `data_abertura` deste caso ate existir, na pasta, um arquivo que traga a data oficial de abertura/sessao.

