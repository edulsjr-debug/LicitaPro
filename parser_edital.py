import re
import unicodedata
from datetime import datetime
from typing import Any, Optional


NAO_IDENTIFICADO = "Não identificado"
NAO_INFORMADO = "Não informado"


MODALIDADES = [
    ("Pregão Eletrônico", ["pregao eletronico", "pregao eletrônico"]),
    ("Pregão Presencial", ["pregao presencial", "pregão presencial"]),
    ("Concorrência Eletrônica", ["concorrencia eletronica", "concorrência eletrônica"]),
    ("Concorrência", ["concorrencia", "concorrência"]),
    ("Dispensa Eletrônica", ["dispensa eletronica", "dispensa eletrônica"]),
    ("Dispensa", ["dispensa"]),
    ("Inexigibilidade", ["inexigibilidade"]),
    ("Tomada de Preços", ["tomada de precos", "tomada de preços"]),
    ("Convite", ["convite"]),
    ("Leilão", ["leilao", "leilão"]),
    ("Credenciamento", ["credenciamento"]),
    ("Chamamento Público", ["chamamento publico", "chamamento público"]),
    ("Diálogo Competitivo", ["dialogo competitivo", "diálogo competitivo"]),
]

ORGAO_PREFIXOS = [
    "prefeitura",
    "municipio",
    "camara",
    "secretaria",
    "ministerio",
    "tribunal",
    "autarquia",
    "fundacao",
    "instituto",
    "departamento",
    "superintendencia",
    "companhia",
    "empresa publica",
    "servico autonomo",
    "consorcio",
]

SEGMENTOS = [
    (
        "Segurança",
        [
            "vigilancia",
            "seguranca patrimonial",
            "portaria",
            "guarita",
            "ronda",
            "monitoramento",
            "cftv",
            "alarme",
        ],
    ),
    (
        "Limpeza e Conservação",
        [
            "limpeza",
            "conservacao",
            "higienizacao",
            "asseio",
            "zeladoria",
            "jardinagem",
            "dedetizacao",
        ],
    ),
    (
        "Manutenção",
        [
            "manutencao",
            "reparo",
            "instalacao",
            "manutencao predial",
            "eletrica",
            "hidraulica",
        ],
    ),
    (
        "Tecnologia e TI",
        [
            "software",
            "sistema",
            "tecnologia",
            "informatica",
            "hardware",
            "licenca",
            "suporte tecnico",
        ],
    ),
    (
        "Obras e Infraestrutura",
        ["obra", "construcao", "reforma", "pavimentacao", "engenharia", "infraestrutura"],
    ),
    ("Saúde", ["saude", "hospital", "medicamento", "medico", "ambulatorial"]),
    ("Alimentação", ["alimentacao", "refeicao", "merenda", "generos alimenticios"]),
    ("Transporte", ["transporte", "veiculo", "frota", "combustivel", "fretamento"]),
]


def _normalizar(texto: str) -> str:
    """Normaliza mantendo tamanho aproximado para facilitar buscas por indice."""
    mapa = {
        "º": "o",
        "ª": "a",
        "°": "o",
        "–": "-",
        "—": "-",
        "\u00a0": " ",
    }
    chars = []
    for char in texto:
        char = mapa.get(char, char)
        decomposto = unicodedata.normalize("NFKD", char)
        base = "".join(c for c in decomposto if not unicodedata.combining(c))
        chars.append((base[:1] if base else char).lower())
    return "".join(chars)


def _limpar_linha(valor: str) -> str:
    valor = re.sub(r"\s+", " ", valor or "").strip(" \t\r\n:-–—")
    return valor.strip()


def _primeiro_grupo(regex: str, texto: str, flags: int = re.IGNORECASE) -> str:
    match = re.search(regex, texto, flags)
    if not match:
        return NAO_IDENTIFICADO
    return _limpar_linha(match.group(1) if match.groups() else match.group(0))


def _is_identificado(valor: Any) -> bool:
    if isinstance(valor, list):
        return bool(valor)
    texto = str(valor or "").strip().lower()
    return bool(texto) and texto not in {
        "não identificado",
        "nao identificado",
        "não informada",
        "nao informada",
        "não informado",
        "nao informado",
        "verificar edital",
        "- verificar edital",
    }


def identificar_secoes(texto: str) -> dict[str, str]:
    secoes: dict[str, list[str]] = {"_cabecalho": []}
    atual = "_cabecalho"

    titulos = {
        "objeto": ["objeto", "do objeto", "objeto da licitacao"],
        "habilitacao": ["habilitacao", "da habilitacao", "documentos de habilitacao"],
        "proposta": ["proposta", "da proposta", "proposta de precos"],
        "julgamento": ["julgamento", "criterio de julgamento"],
        "prazos": ["prazos", "vigencia", "prazo de vigencia"],
        "valor": ["valor estimado", "valor global", "preco estimado", "orcamento estimado"],
    }

    for linha in texto.splitlines():
        limpa = _limpar_linha(linha)
        normalizada = _normalizar(limpa)
        sem_numero = re.sub(r"^\d+(\.\d+)*\s*[-.)]?\s*", "", normalizada)

        nova = None
        if 3 <= len(sem_numero) <= 90:
            for nome, candidatos in titulos.items():
                if any(sem_numero == c or sem_numero.startswith(c + " ") for c in candidatos):
                    nova = nome
                    break

        if nova:
            atual = nova
            secoes.setdefault(atual, []).append(linha)
        else:
            secoes.setdefault(atual, []).append(linha)

    return {nome: "\n".join(linhas).strip() for nome, linhas in secoes.items()}


def extrair_numero_edital(texto: str) -> str:
    normalizado = _normalizar(texto)
    padroes = [
        r"((?:pregao|concorrencia|dispensa|inexigibilidade|chamamento publico|credenciamento)(?:\s+eletronico|\s+presencial)?\s*(?:n|no|numero|nr)?\s*[.:oº°-]*\s*\d+[\w./-]*\s*/\s*\d{2,4})",
        r"((?:edital|processo(?: administrativo)?)\s*(?:n|no|numero|nr)?\s*[.:oº°-]*\s*\d+[\w./-]*\s*/\s*\d{2,4})",
    ]
    for padrao in padroes:
        match = re.search(padrao, normalizado, re.IGNORECASE)
        if match:
            return _limpar_linha(texto[match.start(1) : match.end(1)])
    return NAO_IDENTIFICADO


def extrair_orgao(texto: str) -> str:
    linhas = [_limpar_linha(l) for l in texto.splitlines()[:60]]
    ignorar = ("edital", "pregão", "pregao", "processo", "aviso", "licitação", "licitacao")

    for linha in linhas:
        if len(linha) < 8 or any(t in linha.lower() for t in ignorar):
            continue
        normalizada = _normalizar(linha)
        if any(normalizada.startswith(prefixo) for prefixo in ORGAO_PREFIXOS):
            return linha[:160]

    padroes = [
        r"(?:órgão|orgao|unidade\s+compradora|entidade)\s*[:\-]\s*([^\n]{8,160})",
        r"([A-ZÁÉÍÓÚÀÂÊÔÃÕÇ][^\n]{8,160})\s*\n\s*CNPJ",
    ]
    for padrao in padroes:
        valor = _primeiro_grupo(padrao, texto)
        if _is_identificado(valor):
            return valor[:160]
    return NAO_IDENTIFICADO


def extrair_cnpj(texto: str) -> str:
    return _primeiro_grupo(r"(\d{2}[\.\s]?\d{3}[\.\s]?\d{3}[\/\s]?\d{4}[\-\s]?\d{2})", texto)


def extrair_modalidade(texto: str) -> str:
    normalizado = _normalizar(texto[:5000])
    for nome, variantes in MODALIDADES:
        if any(variante in normalizado for variante in variantes):
            return nome
    return NAO_IDENTIFICADO


def extrair_criterio_julgamento(texto: str) -> str:
    normalizado = _normalizar(texto)
    criterios = [
        ("Menor Preço Global", ["menor preco global"]),
        ("Menor Preço por Item", ["menor preco por item", "menor preco unitario"]),
        ("Menor Preço", ["menor preco", "menor valor"]),
        ("Maior Desconto", ["maior desconto"]),
        ("Técnica e Preço", ["tecnica e preco"]),
        ("Melhor Técnica", ["melhor tecnica"]),
        ("Maior Lance", ["maior lance", "maior oferta"]),
    ]
    for nome, variantes in criterios:
        if any(v in normalizado for v in variantes):
            return nome
    return NAO_IDENTIFICADO


def _secao_por_nome(secoes: dict[str, str], *nomes: str) -> str:
    for nome in nomes:
        for chave, conteudo in secoes.items():
            if nome in chave and conteudo:
                return conteudo
    return ""


def extrair_objeto(texto: str, secoes: Optional[dict[str, str]] = None) -> str:
    secoes = secoes or identificar_secoes(texto)
    secao = _secao_por_nome(secoes, "objeto")
    if secao:
        linhas = []
        for linha in secao.splitlines():
            limpa = _limpar_linha(linha)
            normalizada = _normalizar(limpa)
            if not limpa or normalizada in {"objeto", "do objeto"}:
                continue
            if "objeto" in normalizada and len(normalizada) <= 90:
                continue
            if re.match(r"^\d+(\.\d+)*\s*$", limpa):
                continue
            linhas.append(limpa)
            if sum(len(l) for l in linhas) >= 350:
                break
        if linhas:
            return _limpar_linha(" ".join(linhas))[:600]

    padroes = [
        r"(?:objeto\s*[:\-]\s*)([^\n]{20,600})",
        r"(?:contratação|contratacao|aquisição|aquisicao)\s+de\s+([^\n]{20,600})",
    ]
    for padrao in padroes:
        valor = _primeiro_grupo(padrao, texto)
        if _is_identificado(valor):
            return valor[:600]
    return NAO_IDENTIFICADO


def _valor_float(valor: str) -> float:
    texto = _normalizar(valor)
    match = re.search(r"(\d{1,3}(?:\.\d{3})*(?:,\d{2})?|\d+(?:,\d{2})?)", valor)
    if not match:
        return 0.0
    numero = match.group(1).replace(".", "").replace(",", ".")
    try:
        base = float(numero)
    except ValueError:
        return 0.0
    if "bilhao" in texto or "bilhoes" in texto:
        return base * 1_000_000_000
    if "milhao" in texto or "milhoes" in texto:
        return base * 1_000_000
    if re.search(r"\bmil\b", texto):
        return base * 1_000
    return base


def extrair_valor(texto: str) -> str:
    candidatos: list[tuple[int, float, str]] = []
    for match in re.finditer(r"R\$\s*\d{1,3}(?:\.\d{3})*(?:,\d{2})?|R\$\s*\d+(?:,\d{2})?", texto):
        inicio = max(0, match.start() - 120)
        fim = min(len(texto), match.end() + 40)
        contexto = _normalizar(texto[inicio:fim])
        peso = 0
        if any(p in contexto for p in ["valor estimado", "valor total", "valor global", "preco maximo", "orcamento"]):
            peso += 10
        if any(p in contexto for p in ["unitario", "mensal", "por item"]):
            peso -= 4
        candidatos.append((peso, _valor_float(match.group(0)), _limpar_linha(match.group(0))))

    if not candidatos:
        return NAO_IDENTIFICADO
    candidatos.sort(key=lambda item: (item[0], item[1]), reverse=True)
    return candidatos[0][2]


def extrair_data_abertura(texto: str) -> str:
    datas = []
    padrao = r"\d{1,2}/\d{1,2}/\d{4}(?:\s*(?:às|as|a partir das|[-–])\s*\d{1,2}[:h]\d{2})?"
    for match in re.finditer(padrao, texto, re.IGNORECASE):
        contexto = _normalizar(texto[max(0, match.start() - 140) : match.end() + 80])
        peso = 0
        if any(p in contexto for p in ["abertura", "sessao publica", "recebimento das propostas"]):
            peso += 10
        if any(p in contexto for p in ["publicacao", "assinatura", "vigencia"]):
            peso -= 3
        datas.append((peso, _limpar_linha(match.group(0))))
    if not datas:
        return NAO_IDENTIFICADO
    datas.sort(key=lambda item: item[0], reverse=True)
    return datas[0][1]


def extrair_prazo_vigencia(texto: str) -> str:
    padroes = [
        r"(?:vigência|vigencia|prazo\s+de\s+vigência|prazo\s+de\s+vigencia)[^\n]{0,80}?(\d+)\s*(dias?|meses?|anos?)",
        r"contrato[^\n]{0,120}?(\d+)\s*(dias?|meses?|anos?)",
    ]
    for padrao in padroes:
        match = re.search(padrao, texto, re.IGNORECASE)
        if match:
            return f"{match.group(1)} {match.group(2)}"
    return NAO_IDENTIFICADO


def extrair_prazo_envio_proposta(texto: str) -> str:
    padroes = [
        r"(?:recebimento|envio|encaminhamento)\s+(?:das\s+)?propostas[^\n]{0,120}?(\d{1,2}/\d{1,2}/\d{4}(?:\s*(?:às|as)\s*\d{1,2}[:h]\d{2})?)",
        r"(?:propostas[^\n]{0,80}?até|ate)[^\n]{0,40}?(\d{1,2}/\d{1,2}/\d{4}(?:\s*(?:às|as)\s*\d{1,2}[:h]\d{2})?)",
    ]
    for padrao in padroes:
        valor = _primeiro_grupo(padrao, texto)
        if _is_identificado(valor):
            return valor
    return NAO_IDENTIFICADO


def extrair_documentos_habilitacao(texto: str, secoes: Optional[dict[str, str]] = None) -> list[str]:
    secoes = secoes or identificar_secoes(texto)
    conteudo = _secao_por_nome(secoes, "habilitacao")
    if not conteudo:
        match = re.search(
            r"(habilitação|habilitacao|documentos de habilitação|documentos de habilitacao)([\s\S]{200,3500}?)(?:\n\s*\d+\.?\s*[A-ZÁÉÍÓÚÃÕÇ]{4,}|\Z)",
            texto,
            re.IGNORECASE,
        )
        conteudo = match.group(0) if match else ""

    docs: list[str] = []
    for linha in conteudo.splitlines():
        limpa = _limpar_linha(re.sub(r"^\d+(\.\d+)*\s*[-.)]?\s*", "", linha))
        normalizada = _normalizar(limpa)
        if len(limpa) < 8:
            continue
        if any(
            termo in normalizada
            for termo in [
                "certidao",
                "comprovante",
                "atestado",
                "declaracao",
                "ato constitutivo",
                "contrato social",
                "balanco patrimonial",
                "regularidade",
                "fgts",
                "receita federal",
                "falencia",
                "inscricao estadual",
                "inscricao municipal",
            ]
        ):
            docs.append(limpa[:180])

    unicos = []
    vistos = set()
    for doc in docs:
        chave = _normalizar(doc)
        if chave not in vistos:
            vistos.add(chave)
            unicos.append(doc)
    return unicos[:20]


def detectar_segmento(objeto: str, texto: str = "") -> str:
    base = _normalizar(f"{objeto} {texto[:2500]}")
    for segmento, palavras in SEGMENTOS:
        if any(p in base for p in palavras):
            return segmento
    return "Outros"


def calcular_confianca(campos: dict[str, Any]) -> tuple[int, list[str]]:
    pesos = {
        "numero_edital": 12,
        "orgao": 12,
        "cnpj": 8,
        "modalidade": 10,
        "objeto": 18,
        "valor": 12,
        "data_abertura": 12,
        "prazo_vigencia": 6,
        "criterio_julgamento": 6,
        "documentos_habilitacao": 4,
    }
    faltantes = []
    pontos = 0
    for campo, peso in pesos.items():
        if _is_identificado(campos.get(campo)):
            pontos += peso
        else:
            faltantes.append(campo)
    return min(100, pontos), faltantes


def gerar_ficha(campos: dict[str, Any]) -> str:
    documentos = campos.get("documentos_habilitacao") or []
    docs_md = "\n".join(f"- {doc}" for doc in documentos) if documentos else "- Verificar edital original."
    alertas = []
    if campos.get("faltantes"):
        alertas.append(
            "> Extração local incompleta: revisar "
            + ", ".join(campos["faltantes"][:5]).replace("_", " ")
            + "."
        )
    if campos.get("usar_fallback_api"):
        alertas.append("> Confiança baixa na extração automática; usar análise por IA como complemento.")
    alertas_md = "\n\n".join(alertas) if alertas else "> Nenhum alerta automático identificado."

    return f"""## FICHA DE LICITAÇÃO

| Campo | Valor |
|---|---|
| **Nº / Processo** | {campos.get('numero_edital', NAO_IDENTIFICADO)} |
| **Órgão** | {campos.get('orgao', NAO_IDENTIFICADO)} |
| **Modalidade** | {campos.get('modalidade', NAO_IDENTIFICADO)} |
| **Critério de Julgamento** | {campos.get('criterio_julgamento', NAO_IDENTIFICADO)} |
| **Valor Estimado Total** | {campos.get('valor', NAO_IDENTIFICADO)} |
| **Vigência do Contrato** | {campos.get('prazo_vigencia', NAO_IDENTIFICADO)} |
| **Abertura das Propostas** | {campos.get('data_abertura', NAO_IDENTIFICADO)} |
| **Prazo para Envio de Proposta** | {campos.get('prazo_envio_proposta', NAO_IDENTIFICADO)} |

## Objeto
{campos.get('objeto', NAO_IDENTIFICADO)}

## Condições Financeiras
- **Garantia Contratual:** {NAO_INFORMADO}
- **Prazo de Pagamento:** {NAO_INFORMADO}
- **Patrimônio Líquido Mínimo:** {NAO_INFORMADO}
- **Capital Social Mínimo:** {NAO_INFORMADO}

## Posto de Atendimento
{NAO_INFORMADO}

## Contato do Órgão
{NAO_INFORMADO}

## Itens a Cotar

| # | Descrição | Unid. | Qtd. | Valor Unit. | Valor Total |
|---|-----------|-------|------|-------------|-------------|
| 1 | Verificar edital original | {NAO_INFORMADO} | {NAO_INFORMADO} | {NAO_INFORMADO} | {campos.get('valor', NAO_IDENTIFICADO)} |

## Modelo de Proposta
{NAO_INFORMADO}

## Documentos de Habilitação

### Jurídica, Fiscal, Trabalhista, Econômico-Financeira e Técnica
{docs_md}

## ⚠️ Alertas
{alertas_md}

## Score de Viabilidade
**Score:** {campos.get('score', 0)}
**Nível:** {campos.get('nivel', 'Média')}
**Justificativa:** Campos principais extraídos automaticamente. Confiança da extração: {campos.get('confianca', 0)}%.

---
*Fonte: extração automática sem API. Processado em {datetime.now().strftime('%d/%m/%Y %H:%M')}.*
""".strip()


def analisar_sem_api(texto: str, min_confianca: int = 70) -> dict[str, Any]:
    secoes = identificar_secoes(texto)
    objeto = extrair_objeto(texto, secoes)
    campos: dict[str, Any] = {
        "numero_edital": extrair_numero_edital(texto),
        "orgao": extrair_orgao(texto),
        "cnpj": extrair_cnpj(texto),
        "modalidade": extrair_modalidade(texto),
        "objeto": objeto,
        "valor": extrair_valor(texto),
        "data_abertura": extrair_data_abertura(texto),
        "prazo_envio_proposta": extrair_prazo_envio_proposta(texto),
        "prazo_vigencia": extrair_prazo_vigencia(texto),
        "criterio_julgamento": extrair_criterio_julgamento(texto),
        "documentos_habilitacao": extrair_documentos_habilitacao(texto, secoes),
        "segmento": detectar_segmento(objeto, texto),
    }
    confianca, faltantes = calcular_confianca(campos)
    campos["confianca"] = confianca
    campos["faltantes"] = faltantes
    campos["usar_fallback_api"] = confianca < min_confianca
    campos["score"] = max(30, min(95, confianca))
    campos["nivel"] = "Alta" if confianca >= 80 else "Média" if confianca >= 55 else "Baixa"
    campos["ficha"] = gerar_ficha(campos)
    return campos
