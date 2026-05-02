import re
import unicodedata
from datetime import datetime
from typing import Any, Optional


NAO_IDENTIFICADO = "Não identificado"
NAO_INFORMADO = "Não informado"


MODALIDADES = [
    ("Comparação de Preços", ["comparacao de precos", "comparacao de preco"]),
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
    "conselho",
    "agencia",
    "colegio",
    "ordem",
    "fundo",
    "associacao",
    "universidade",
    "hospital",
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
    ("Viagens e Passagens", ["passagem aerea", "passagens aereas", "agenciamento de viagens", "bilhete aereo", "bilhetes aereos", "seguro viagem", "hospedagem"]),
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
    original = texto[:5000]
    normalizado = _normalizar(original)  # mesmo comprimento — posições alinhadas

    padroes_prioritarios = [
        # sigla curta seguida direto do número: "PE N° 03/2026", "SRP Nº 01/2025"
        re.compile(
            r"\b((?:pe|cp|tp|cc|rdc|srp|pp|ine)\s*(?:n|no|numero|nr)?\s*[.:ºo°-]?\s*\d{1,6}[./-]\d{2,4})\b",
            re.IGNORECASE,
        ),
        # modalidade + texto intermediário opcional (srp, eletrônico, etc.) + número
        re.compile(
            r"\b((?:pregao(?:\s+eletronico|\s+presencial)?|"
            r"concorrencia(?:\s+eletronica|\s+publica)?|"
            r"tomada\s+de\s+precos?|dispensa(?:\s+eletronica)?|"
            r"inexigibilidade|chamamento\s+publico|credenciamento|"
            r"rdc|dialogo\s+competitivo)"
            r"(?:\s+(?:eletronico|presencial|eletronica|publica|srp|ine))?"
            r"(?:\s+srp)?"
            r"\s*(?:n|no|numero|nr)?\s*[.:ºo°-]?\s*\d{1,6}[./-]\d{2,4})\b",
            re.IGNORECASE,
        ),
    ]
    padroes_secundarios = [
        re.compile(
            r"\b((?:edital|processo(?:\s+administrativo)?)\s*"
            r"(?:n|no|numero|nr)?\s*[.:ºo°-]?\s*\d{1,6}[./-]\d{4})\b",
            re.IGNORECASE,
        ),
        re.compile(
            r"\b((?:aviso)\s+(?:de\s+)?(?:licitacao|licitação|pregao|pregão)[^\n]{0,40}?"
            r"(?:n|no|numero|nr)?\s*[.:ºo°-]?\s*\d{1,6}[./-]\d{2,4})\b",
            re.IGNORECASE,
        ),
    ]

    def _valido(candidato: str) -> bool:
        c = _normalizar(candidato)
        if re.search(r"\bart\.?\s*\d+\.\d+\b", c):
            return False
        if re.search(r"\bcl[aá]usula\s*\d+\.\d+\b", c):
            return False
        if re.search(r"\bitem\s*\d+\.\d+\b", c):
            return False
        return True

    for padroes in (padroes_prioritarios, padroes_secundarios):
        for padrao in padroes:
            match = padrao.search(normalizado)
            if match:
                # extrai do texto original na mesma posição (normalizar preserva comprimento)
                candidato = _limpar_linha(original[match.start(1):match.end(1)])
                if _valido(candidato):
                    return candidato

    return NAO_IDENTIFICADO

def extrair_orgao(texto: str) -> str:
    linhas = [_limpar_linha(l) for l in texto.splitlines()[:80]]
    ignorar = (
        "edital", "pregão", "pregao", "processo", "aviso", "licitação",
        "licitacao", "termo de referencia", "anexo", "objeto",
    )

    # busca etiquetas só no cabeçalho (primeiros 5000 chars) para não pegar
    # cláusulas como "Contratante: a) Em caso de atraso..." no corpo do contrato
    cabecalho = re.sub(r"\s+", " ", texto[:8000])
    etiquetas = [
        (r"(?:órgão|orgao|unidade\s+compradora|unidade\s+gestora|entidade)\s*[:\-]\s*([^\n]{5,180})", False),
        (r"(?:órgão|orgao)\s+responsável\s*[:\-]\s*([^\n]{5,180})", False),
        # "contratante:" aceito apenas se a linha não parece cláusula (sem "caso", "atraso", "obrigação")
        (r"(?:contratante)\s*[:\-]\s*([^\n]{5,180})", True),
        # "nome:" e "razão social:" aceitos somente se o valor começa com prefixo de órgão
        (r"(?:nome|razao\s+social)\s*[:\-]\s*([^\n]{5,180})", True),
    ]
    for padrao, precisa_prefixo in etiquetas:
        match = re.search(padrao, cabecalho, re.IGNORECASE)
        if not match:
            continue
        valor = _limpar_linha(match.group(1) if match.groups() else match.group(0))
        if not _is_identificado(valor):
            continue
        valor = _limpar_linha(
            re.split(
                r"\b(?:projeto|endere[cç]o|cidade|uf|cnpj|telefone|e-?mail)\b\s*:?",
                valor,
                maxsplit=1,
                flags=re.IGNORECASE,
            )[0]
        )
        if _normalizar(valor).endswith(" para"):
            for prox in cabecalho[match.end():].splitlines()[:4]:
                prox_limpa = _limpar_linha(prox)
                prox_norm = _normalizar(prox_limpa)
                if not prox_limpa:
                    continue
                if re.match(r"^(projeto|endereco|cidade|uf|cnpj|telefone|e-?mail)\b", prox_norm):
                    break
                valor = _limpar_linha(f"{valor} {prox_limpa}")
                break
        if "instituto interamericano de cooperacao para a agricultura" in _normalizar(valor):
            valor = "INSTITUTO INTERAMERICANO DE COOPERAÇÃO PARA A AGRICULTURA"
        if precisa_prefixo:
            val_norm = _normalizar(valor)
            if not any(val_norm.startswith(p) for p in ORGAO_PREFIXOS):
                continue
        return valor[:180]

    for linha in linhas:
        if len(linha) < 8:
            continue
        baixa = _normalizar(linha)
        if any(t in baixa for t in ignorar):
            continue
        if any(baixa.startswith(prefixo) for prefixo in ORGAO_PREFIXOS):
            return linha[:180]

    for linha in linhas[:40]:
        baixa = _normalizar(linha)
        if not baixa or len(baixa) > 140:
            continue
        # linha toda em maiúsculas com 2+ palavras (ex: "CAMARA MUNICIPAL DE FOO")
        linha_strip = linha.strip()
        if len(linha_strip) >= 8 and linha_strip == linha_strip.upper() and len(linha_strip.split()) >= 2:
            if not re.search(r"\b(?:edital|aviso|processo|pregao|pregão|precos|cotacao|comparacao|chamamento)\b", baixa):
                if not re.search(r"\d+[./]\d{4}\b", baixa):  # rejeita se parece número de processo
                    return _limpar_linha(linha)[:180]
        # sigla/nome de organismo reconhecido (mínimo 3 chars para capturar "IICA")
        if len(baixa) >= 3 and re.search(r"\b(iica|onu|unesco|oms|banco|instituto|fundacao|fundação|agencia|agência|associacao|associação)\b", baixa):
            return _limpar_linha(linha)[:180]

    for padrao in (
        r"([A-ZÁÉÍÓÚÀÂÊÔÃÕÇ][^\n]{5,180})\s*\n\s*CNPJ",
        r"([A-ZÁÉÍÓÚÀÂÊÔÃÕÇ][^\n]{5,180})\s*\n\s*CPF",
    ):
        valor = _primeiro_grupo(padrao, texto)
        if _is_identificado(valor):
            return valor[:180]

    return NAO_IDENTIFICADO


def extrair_cnpj(texto: str) -> str:
    return _primeiro_grupo(r"(\d{2}[\.\s]?\d{3}[\.\s]?\d{3}[\/\s]?\d{4}[\-\s]?\d{2})", texto)


def extrair_modalidade(texto: str) -> str:
    normalizado = re.sub(r"\s+", " ", _normalizar(texto[:5000]))
    for nome, variantes in MODALIDADES:
        if any(variante in normalizado for variante in variantes):
            return nome
    if re.search(r"pregao|preg?o", normalizado) and re.search(r"eletronico|eletr?nico", normalizado):
        return "Preg?o Eletr?nico"
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
    texto_norm = _normalizar(texto)
    contexto_valor_forte = [
        "valor estimado total", "valor total estimado", "valor global",
        "valor estimado da contratacao", "valor da contratacao",
        "valor maximo estimado", "valor maximo global", "orcamento estimado",
    ]
    contexto_valor = [
        *contexto_valor_forte,
        "valor estimado",
        "preco maximo", "preco de referencia", "valor de referencia",
        "valor maximo", "custo estimado", "orcamento", "dotacao",
        "estimativa", "valor anual", "valor mensal", "valor total",
    ]
    contexto_parcial = [
        "taxa de agenciamento", "taxa administrativa", "taxa de administracao",
        "valor da taxa", "percentual", "maior desconto", "desconto",
        "valor unitario", "unitario", "por bilhete", "por item", "itens",
        "lance minimo", "valor minimo",
    ]
    padroes = [
        re.compile(r"(?:r\$|rs)\s*([\d]{1,3}(?:\.[\d]{3})*(?:,\d{2})?|[\d]+(?:,\d{2})?)", re.IGNORECASE),
        re.compile(r"\b([\d]{1,3}(?:\.[\d]{3})+(?:,\d{2})?)\b", re.IGNORECASE),
        re.compile(r"\b([\d]{5,}(?:,\d{2})?)\b", re.IGNORECASE),
    ]

    def parse_valor_numerico(s: str) -> float:
        limpo = re.sub(r"[^\d,]", "", s)
        if not limpo:
            return 0.0
        limpo = limpo.replace(".", "").replace(",", ".")
        try:
            return float(limpo)
        except ValueError:
            return 0.0

    def score_contexto(contexto: str) -> int:
        score = 0
        if any(kw in contexto for kw in contexto_valor_forte):
            score += 18
        if any(kw in contexto for kw in contexto_valor):
            score += 10
        if any(kw in contexto for kw in contexto_parcial):
            score -= 14
        if any(kw in contexto for kw in ("r$", "rs", "reais")):
            score += 2
        return score

    def aceitar_candidato(contexto: str, num: float) -> bool:
        if num <= 0:
            return False
        if num < 100:
            return False
        forte = any(kw in contexto for kw in contexto_valor_forte)
        parcial = any(kw in contexto for kw in contexto_parcial)
        if parcial and not forte:
            return False
        return True

    candidatos: list[tuple[int, float, str]] = []
    for ctx in contexto_valor:
        pos = texto_norm.find(ctx)
        while pos != -1:
            inicio = max(0, pos - 80)
            fim = min(len(texto), pos + 260)
            janela = texto[inicio:fim]
            janela_norm = texto_norm[inicio:fim]
            for padrao in padroes:
                for m in padrao.finditer(janela):
                    num = parse_valor_numerico(m.group(1))
                    if not aceitar_candidato(janela_norm, num):
                        continue
                    candidatos.append((score_contexto(janela_norm), num, f"R$ {m.group(1)}"))
            pos = texto_norm.find(ctx, pos + 1)

    if not candidatos:
        for padrao in padroes[:2]:
            for m in padrao.finditer(texto):
                inicio = max(0, m.start() - 120)
                fim = min(len(texto), m.end() + 80)
                contexto = texto_norm[inicio:fim]
                num = parse_valor_numerico(m.group(1))
                if not aceitar_candidato(contexto, num):
                    continue
                candidatos.append((score_contexto(contexto), num, f"R$ {m.group(1)}"))

    if not candidatos:
        return NAO_IDENTIFICADO

    candidatos.sort(key=lambda item: (item[0], item[1]), reverse=True)
    return candidatos[0][2]

def extrair_data_abertura(texto: str) -> str:
    datas: list[tuple[int, str]] = []
    texto_norm = _normalizar(texto)
    anos_edital = re.findall(
        r"\b(?:edital|pregao|processo|srp|pe|cp|tp|cc)\s*(?:n[ºo.]*)?\s*\d{1,5}[./-](20\d{2})\b",
        texto_norm[:6000],
        re.IGNORECASE,
    )
    ano_referencia = anos_edital[0] if anos_edital else ""
    positivos_fortes = [
        "data de abertura",
        "abertura da sessao",
        "abertura das propostas",
        "sessao publica",
        "inicio da sessao",
        "sessao de disputa",
        "inicio da disputa",
        "recebimento das propostas",
        "recebimento de propostas",
        "recebimento da proposta",
        "apresentacao das propostas",
        "apresentacao de propostas",
        "entrega das propostas",
        "entrega de propostas",
        "data limite",
        "data de entrega",
        "prazo para apresentacao",
        "prazo de apresentacao",
        "prazo para envio",
        "prazo de envio",
        "limite para recebimento",
        "envio de proposta",
        "propostas ate",
        "realizacao do certame",
    ]
    positivos_medios = ["abertura", "sessao", "propostas", "certame", "disputa", "lances"]
    negativos = [
        "publicacao",
        "publicado",
        "assinatura",
        "emissao",
        "vigencia",
        "lei",
        "decreto",
        "portaria",
        "resolucao",
        "instrucao normativa",
        "referencia",
        "data base",
        "reajuste",
        "validade",
        "contrato",
        "edicao",
        "expedido",
        "atualizacao",
    ]
    padrao = r"\d{1,2}/\d{1,2}/\d{4}(?:\s*(?:às|as|a partir das|[-–])\s*\d{1,2}[:h]\d{2})?"
    for match in re.finditer(padrao, texto, re.IGNORECASE):
        valor = _limpar_linha(match.group(0))
        contexto = _normalizar(texto[max(0, match.start() - 220) : match.end() + 140])
        contexto_anterior = _normalizar(texto[max(0, match.start() - 50) : match.start()])
        peso = 0
        if any(p in contexto for p in positivos_fortes):
            peso += 18
        elif any(p in contexto for p in positivos_medios):
            peso += 7
        if (
            match.start() < 4000
            and re.search(r"\bdata\s*$", contexto_anterior)
            and any(p in contexto for p in ["comparacao de precos", "shopping numero", "dados do solicitante"])
        ):
            peso += 18
        if (
            match.start() < 4000
            and "comparacao de precos" in contexto
            and "data" in contexto
            and "dados do solicitante" in contexto
        ):
            peso += 14
        if any(p in contexto for p in negativos):
            peso -= 12
        if re.search(r"\d{1,2}[:h]\d{2}", valor):
            peso += 5
        ano_match = re.search(r"/(20\d{2})", valor)
        if ano_referencia and ano_match and ano_match.group(1) == ano_referencia:
            peso += 3
        datas.append((peso, valor))
    if not datas:
        return NAO_IDENTIFICADO
    datas.sort(key=lambda item: item[0], reverse=True)
    if datas[0][0] < 6:
        return NAO_IDENTIFICADO
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


_SEGMENTOS_ESPECIFICOS = [
    # termos inequívocos que valem mais que qualquer coincidência genérica
    ("Viagens e Passagens", ["passagem aerea", "passagens aereas", "agenciamento de viagens", "bilhete aereo", "bilhetes aereos", "seguro viagem", "hospedagem"]),
    ("Transporte", ["fretamento de aeronave", "locacao de veiculo", "transporte de passageiros"]),
    ("Segurança", ["vigilancia patrimonial", "portaria remota", "monitoramento eletronico", "circuito fechado"]),
    ("Limpeza e Conservação", ["limpeza e conservacao", "asseio e conservacao", "servicos de limpeza"]),
    ("Manutenção", ["manutencao predial", "manutencao eletrica", "manutencao hidraulica"]),
]


def detectar_segmento(objeto: str, texto: str = "") -> str:
    base_objeto = _normalizar(objeto)
    base_texto = _normalizar(texto[:1500])
    # 1ª passagem: termos específicos e inequívocos no objeto
    for segmento, palavras in _SEGMENTOS_ESPECIFICOS:
        if any(p in base_objeto for p in palavras):
            return segmento
    # 2ª passagem: lista geral contra o objeto
    for segmento, palavras in SEGMENTOS:
        if any(p in base_objeto for p in palavras):
            return segmento
    # fallback: início do texto completo
    for segmento, palavras in _SEGMENTOS_ESPECIFICOS:
        if any(p in base_texto for p in palavras):
            return segmento
    for segmento, palavras in SEGMENTOS:
        if any(p in base_texto for p in palavras):
            return segmento
    return "Outros"


def calcular_score_viabilidade(campos: dict[str, Any]) -> tuple[int, str, list[str]]:
    """Score de viabilidade real da licitação (não mede qualidade da extração).

    Dimensões:
      - Aderência ao segmento  0–40
      - Atratividade financeira 0–25
      - Competitividade         0–20  (modalidade + critério)
      - Duração do contrato     0–15
    """
    justificativas: list[str] = []
    total = 0

    # 1. Aderência ao segmento (0–40)
    segmento = campos.get("segmento", "Outros")
    pts_seg = {
        "Segurança": 40, "Limpeza e Conservação": 35, "Manutenção": 25,
        "Viagens e Passagens": 20,
        "Obras e Infraestrutura": 10, "Tecnologia e TI": 8,
        "Transporte": 6, "Saúde": 5, "Alimentação": 5, "Outros": 5,
    }.get(segmento, 5)
    total += pts_seg
    justificativas.append(f"Segmento {segmento}: {pts_seg}/40 pts")

    # 2. Atratividade financeira (0–25)
    valor_str = campos.get("valor", "")
    valor_num = _valor_float(valor_str) if _is_identificado(valor_str) else 0
    if valor_num <= 0:
        pts_fin, desc_fin = 0, "valor não identificado"
    elif valor_num < 30_000:
        pts_fin, desc_fin = 5, "muito baixo"
    elif valor_num < 100_000:
        pts_fin, desc_fin = 12, "baixo"
    elif valor_num < 500_000:
        pts_fin, desc_fin = 20, "médio"
    elif valor_num < 2_000_000:
        pts_fin, desc_fin = 25, "atrativo"
    elif valor_num < 10_000_000:
        pts_fin, desc_fin = 18, "alto"
    else:
        pts_fin, desc_fin = 10, "muito alto"
    total += pts_fin
    justificativas.append(f"Valor {desc_fin} ({valor_str or 'não identificado'}): {pts_fin}/25 pts")

    # 3. Competitividade: modalidade + critério (0–20)
    mod_norm = _normalizar(campos.get("modalidade", ""))
    crit_norm = _normalizar(campos.get("criterio_julgamento", ""))
    if "inexigibilidade" in mod_norm:
        pts_comp, desc_comp = 20, "inexigibilidade (sem concorrência)"
    elif "dispensa" in mod_norm:
        pts_comp, desc_comp = 16, "dispensa (baixa concorrência)"
    elif "chamamento" in mod_norm:
        pts_comp, desc_comp = 13, "chamamento público"
    elif "tomada" in mod_norm:
        pts_comp, desc_comp = 12, "tomada de preços"
    elif "tecnica e preco" in crit_norm or "melhor tecnica" in crit_norm:
        pts_comp, desc_comp = 13, "técnica e preço (qualidade valorizada)"
    elif "maior desconto" in crit_norm:
        pts_comp, desc_comp = 9, "maior desconto"
    elif "menor preco" in crit_norm:
        pts_comp, desc_comp = 7, "menor preço (alta concorrência)"
    else:
        pts_comp, desc_comp = 8, "modalidade padrão"
    total += pts_comp
    justificativas.append(f"Competitividade ({desc_comp}): {pts_comp}/20 pts")

    # 4. Duração do contrato (0–15)
    prazo_str = campos.get("prazo_vigencia", "")
    meses = 0
    if _is_identificado(prazo_str):
        m = re.search(r"(\d+)\s*(dia|mes|ano)", _normalizar(prazo_str))
        if m:
            n, un = int(m.group(1)), m.group(2)
            meses = n * 12 if "ano" in un else (n if "mes" in un else n // 30)
    if meses <= 0:
        pts_dur, desc_dur = 8, "prazo não identificado (assume 12 meses)"
    elif meses >= 24:
        pts_dur, desc_dur = 15, "longo (≥24 meses)"
    elif meses >= 12:
        pts_dur, desc_dur = 12, "adequado (12–23 meses)"
    elif meses >= 6:
        pts_dur, desc_dur = 8, "curto (6–11 meses)"
    else:
        pts_dur, desc_dur = 4, "muito curto (<6 meses)"
    total += pts_dur
    justificativas.append(f"Duração {desc_dur}: {pts_dur}/15 pts")

    total = max(10, min(100, total))
    nivel = "Alta" if total >= 75 else "Média" if total >= 50 else "Baixa"
    return total, nivel, justificativas


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
**{campos.get('score', 0)}/100 — {campos.get('nivel', 'Média')}**

{chr(10).join('- ' + j for j in campos.get('justificativas_score', []))}

## Confiança da Extração
**{campos.get('confianca', 0)}%** dos campos identificados automaticamente.{(' Campos faltantes: ' + ', '.join(campos.get('faltantes', [])).replace('_', ' ') + '.') if campos.get('faltantes') else ''}

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

    score, nivel, justificativas = calcular_score_viabilidade(campos)
    campos["score"] = score
    campos["nivel"] = nivel
    campos["justificativas_score"] = justificativas

    campos["ficha"] = gerar_ficha(campos)
    return campos
