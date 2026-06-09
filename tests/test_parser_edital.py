import unittest

import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from parser_edital import analisar_sem_api, _is_identificado


class ParserEditalTest(unittest.TestCase):
    def test_extrai_campos_essenciais_de_pregao(self):
        texto = """
        PREFEITURA MUNICIPAL DE PORTO ALEGRE
        CNPJ 92.963.560/0001-60

        PREGÃO ELETRÔNICO Nº 071/2026
        Critério de julgamento: Menor Preço Global

        1. DO OBJETO
        Contratação de empresa especializada para prestação de serviços de
        vigilância patrimonial armada e portaria, com fornecimento de mão de obra.

        Valor estimado total: R$ 150.000,00
        Abertura da sessão pública: 15/05/2026 às 09:00
        O contrato terá vigência de 12 meses.

        8. DOCUMENTOS DE HABILITAÇÃO
        Certidão negativa de débitos relativos aos tributos federais.
        Comprovante de regularidade perante o FGTS.
        Atestado de capacidade técnica compatível com o objeto.
        """

        resultado = analisar_sem_api(texto)

        self.assertGreaterEqual(resultado["confianca"], 70)
        self.assertFalse(resultado["usar_fallback_api"])
        self.assertIn("071/2026", resultado["numero_edital"])
        self.assertEqual(resultado["modalidade"], "Pregão Eletrônico")
        self.assertEqual(resultado["criterio_julgamento"], "Menor Preço Global")
        self.assertEqual(resultado["segmento"], "Segurança")
        self.assertNotIn("DO OBJETO", resultado["objeto"])
        self.assertEqual(resultado["valor"], "R$ 150.000,00")
        self.assertIn("15/05/2026", resultado["data_abertura"])
        self.assertIn("## FICHA DE LICITAÇÃO", resultado["ficha"])
        self.assertNotIn("Revisão manual recomendada", resultado["ficha"])
        self.assertNotIn("não substitui análise jurídica", resultado["ficha"])

    def test_baixa_confianca_aciona_fallback(self):
        resultado = analisar_sem_api("Documento sem estrutura reconhecivel.", min_confianca=70)

        self.assertLess(resultado["confianca"], 70)
        self.assertTrue(resultado["usar_fallback_api"])
        self.assertIn("Confiança baixa", resultado["ficha"])

    def test_nao_usa_taxa_simbolica_como_valor_total(self):
        texto = """
        CONSELHO REGIONAL DE PSICOLOGIA
        PREGÃO ELETRÔNICO Nº 02/2026
        Objeto: contratação de empresa para agenciamento de viagens.
        A proposta deverá considerar taxa de agenciamento no valor mínimo de R$ 0,01
        por bilhete emitido, conforme planilha de lances.
        """

        resultado = analisar_sem_api(texto)

        self.assertEqual(resultado["valor"], "Não identificado")
        self.assertEqual(resultado["segmento"], "Viagens e Passagens")

    def test_identifica_comparacao_de_precos(self):
        texto = """
        INSTITUTO INTERAMERICANO DE COOPERACAO PARA A AGRICULTURA
        COMPARAÇÃO DE PREÇOS CP 71.2026
        Objeto: emissão de passagens aéreas nacionais e internacionais.
        Valor estimado total: R$ 250.000,00
        Data de abertura: 09/04/2026
        """

        resultado = analisar_sem_api(texto)

        self.assertEqual(resultado["modalidade"], "Comparação de Preços")
        self.assertEqual(resultado["segmento"], "Viagens e Passagens")
        self.assertEqual(resultado["valor"], "R$ 250.000,00")


    def test_nao_usa_data_legal_como_abertura(self):
        texto = """
        CONSELHO REGIONAL DE PSICOLOGIA
        PREGAO ELETRONICO No 02/2026
        Objeto: contratacao de empresa para agenciamento de viagens.
        O contrato tera vigencia a partir de 01/01/2025 e seguira a lei vigente.
        Valor estimado total: R$ 320.000,00
        """

        resultado = analisar_sem_api(texto)

        self.assertFalse(_is_identificado(resultado["data_abertura"]))
        self.assertNotIn("01/01/2025", resultado["data_abertura"])

    def test_usa_data_de_cabecalho_em_comparacao_de_precos(self):
        texto = """
        COMPARACAO DE PRECOS / SHOPPING NUMERO
        071/2026
        DATA
        09/04/2026
        DADOS DO SOLICITANTE
        NOME: INSTITUTO INTERAMERICANO DE COOPERACAO PARA
        A AGRICULTURA.
        PROJETO: INFORMACOES FLORESTAIS
        Objeto: emissao de passagens aereas nacionais e internacionais.
        Valor estimado total: R$ 250.000,00
        """

        resultado = analisar_sem_api(texto)

        self.assertIn("09/04/2026", resultado["data_abertura"])
        self.assertIn("AGRICULTURA", resultado["orgao"].upper())
        self.assertNotIn("PROJETO", resultado["orgao"].upper())


from main import _mesclar_resultado_ia
from parser_edital import NAO_IDENTIFICADO


class MesclarResultadoIATest(unittest.TestCase):

    def _resultado_base(self):
        """Dict mínimo que analisar_sem_api() retornaria com confiança baixa."""
        return {
            "numero_edital": NAO_IDENTIFICADO,
            "orgao": "Prefeitura de São Paulo",
            "cnpj": NAO_IDENTIFICADO,
            "modalidade": NAO_IDENTIFICADO,
            "objeto": "Aquisição de computadores",
            "valor": NAO_IDENTIFICADO,
            "data_abertura": NAO_IDENTIFICADO,
            "prazo_envio_proposta": NAO_IDENTIFICADO,
            "prazo_vigencia": NAO_IDENTIFICADO,
            "criterio_julgamento": NAO_IDENTIFICADO,
            "documentos_habilitacao": [],
            "segmento": "Tecnologia",
            "confianca": 30,
            "faltantes": ["numero_edital", "cnpj", "modalidade", "valor",
                          "data_abertura", "prazo_vigencia", "criterio_julgamento"],
            "usar_fallback_api": True,
            "score": 20,
            "nivel": "BAIXA",
            "justificativas_score": [],
            "ficha": "## FICHA placeholder",
        }

    def test_campos_faltantes_sao_preenchidos_pela_ia(self):
        resultado = self._resultado_base()
        dados_ia = {
            "numero_edital": "PE 001/2026",
            "orgao": None,
            "cnpj": "46.395.000/0001-39",
            "modalidade": "Pregão Eletrônico",
            "objeto": None,
            "valor": "R$ 120.000,00",
            "data_abertura": "15/07/2026 09:00",
            "prazo_envio_proposta": None,
            "prazo_vigencia": "12 meses",
            "criterio_julgamento": "Menor Preço",
            "documentos_habilitacao": [],
        }

        resultado_final = _mesclar_resultado_ia(resultado, dados_ia)

        self.assertEqual(resultado_final["numero_edital"], "PE 001/2026")
        self.assertEqual(resultado_final["cnpj"], "46.395.000/0001-39")
        self.assertEqual(resultado_final["valor"], "R$ 120.000,00")
        self.assertEqual(resultado_final["data_abertura"], "15/07/2026 09:00")
        self.assertEqual(resultado_final["prazo_vigencia"], "12 meses")
        self.assertEqual(resultado_final["criterio_julgamento"], "Menor Preço")

    def test_parser_nao_e_sobrescrito_quando_ja_identificado(self):
        resultado = self._resultado_base()
        dados_ia = {
            "numero_edital": None,
            "orgao": "NOME ERRADO QUE A IA INVENTOU",
            "cnpj": None,
            "modalidade": None,
            "objeto": "Objeto errado da IA",
            "valor": None,
            "data_abertura": None,
            "prazo_envio_proposta": None,
            "prazo_vigencia": None,
            "criterio_julgamento": None,
            "documentos_habilitacao": [],
        }

        resultado_final = _mesclar_resultado_ia(resultado, dados_ia)

        self.assertEqual(resultado_final["orgao"], "Prefeitura de São Paulo")
        self.assertEqual(resultado_final["objeto"], "Aquisição de computadores")

    def test_documentos_habilitacao_sao_merged_sem_duplicatas(self):
        resultado = self._resultado_base()
        resultado["documentos_habilitacao"] = ["Certidão FGTS", "Contrato social"]
        dados_ia = {
            "numero_edital": None,
            "orgao": None,
            "cnpj": None,
            "modalidade": None,
            "objeto": None,
            "valor": None,
            "data_abertura": None,
            "prazo_envio_proposta": None,
            "prazo_vigencia": None,
            "criterio_julgamento": None,
            "documentos_habilitacao": ["Contrato social", "Balanço patrimonial"],
        }

        resultado_final = _mesclar_resultado_ia(resultado, dados_ia)
        docs = resultado_final["documentos_habilitacao"]

        self.assertIn("Certidão FGTS", docs)
        self.assertIn("Contrato social", docs)
        self.assertIn("Balanço patrimonial", docs)
        self.assertEqual(docs.count("Contrato social"), 1)

    def test_confianca_e_recalculada_apos_merge(self):
        resultado = self._resultado_base()
        dados_ia = {
            "numero_edital": "PE 001/2026",
            "orgao": None,
            "cnpj": "46.395.000/0001-39",
            "modalidade": "Pregão Eletrônico",
            "objeto": None,
            "valor": "R$ 120.000,00",
            "data_abertura": "15/07/2026 09:00",
            "prazo_envio_proposta": None,
            "prazo_vigencia": "12 meses",
            "criterio_julgamento": "Menor Preço",
            "documentos_habilitacao": [],
        }
        confianca_antes = resultado["confianca"]

        resultado_final = _mesclar_resultado_ia(resultado, dados_ia)

        self.assertGreater(resultado_final["confianca"], confianca_antes)
        self.assertFalse(resultado_final["usar_fallback_api"])

    def test_ficha_markdown_e_regenerada(self):
        resultado = self._resultado_base()
        dados_ia = {
            "numero_edital": "PE 001/2026",
            "orgao": None,
            "cnpj": None,
            "modalidade": "Pregão Eletrônico",
            "objeto": None,
            "valor": "R$ 120.000,00",
            "data_abertura": "15/07/2026 09:00",
            "prazo_envio_proposta": None,
            "prazo_vigencia": None,
            "criterio_julgamento": None,
            "documentos_habilitacao": [],
        }

        resultado_final = _mesclar_resultado_ia(resultado, dados_ia)

        self.assertIn("## FICHA DE LICITAÇÃO", resultado_final["ficha"])
        self.assertIn("PE 001/2026", resultado_final["ficha"])
        self.assertIn("R$ 120.000,00", resultado_final["ficha"])


import json
import asyncio
from unittest.mock import patch, AsyncMock


class ExtrairCamposFaltantesGeminiTest(unittest.TestCase):

    def _run(self, coro):
        return asyncio.run(coro)

    def test_retorna_dict_com_campos_extraidos(self):
        from main import _extrair_campos_faltantes_gemini
        dados_esperados = {
            "numero_edital": "PE 042/2026",
            "orgao": None,
            "cnpj": "12.345.678/0001-99",
            "modalidade": None,
            "objeto": None,
            "valor": "R$ 50.000,00",
            "data_abertura": None,
            "prazo_envio_proposta": None,
            "prazo_vigencia": None,
            "criterio_julgamento": None,
            "documentos_habilitacao": [],
        }
        resposta_gemini = json.dumps(dados_esperados)

        with patch("main._executar_requisicao_gemini_sincrona", return_value=resposta_gemini), \
             patch("main._gemini_api_key", "fake-key"):
            resultado = self._run(
                _extrair_campos_faltantes_gemini(
                    texto="texto de teste",
                    campos_extraidos={"orgao": "Prefeitura"},
                    faltantes=["numero_edital", "cnpj", "valor"],
                )
            )

        self.assertEqual(resultado["numero_edital"], "PE 042/2026")
        self.assertEqual(resultado["valor"], "R$ 50.000,00")
        self.assertIsNone(resultado["orgao"])

    def test_lanca_http_exception_sem_api_key(self):
        from fastapi import HTTPException
        from main import _extrair_campos_faltantes_gemini

        with patch("main._gemini_api_key", None):
            with self.assertRaises(HTTPException) as ctx:
                self._run(
                    _extrair_campos_faltantes_gemini(
                        texto="x",
                        campos_extraidos={},
                        faltantes=["valor"],
                    )
                )
        self.assertEqual(ctx.exception.status_code, 503)

    def test_retry_em_429_e_cai_em_503_apos_esgotar(self):
        import urllib.error
        from fastapi import HTTPException
        from main import _extrair_campos_faltantes_gemini

        erro_429 = urllib.error.HTTPError(url="", code=429, msg="rate limit", hdrs=None, fp=None)  # type: ignore

        with patch("main._executar_requisicao_gemini_sincrona", side_effect=erro_429), \
             patch("main._gemini_api_key", "fake-key"), \
             patch("asyncio.sleep", new_callable=AsyncMock):
            with self.assertRaises(HTTPException) as ctx:
                self._run(
                    _extrair_campos_faltantes_gemini(
                        texto="x",
                        campos_extraidos={},
                        faltantes=["valor"],
                        max_tentativas=2,
                    )
                )
        self.assertEqual(ctx.exception.status_code, 503)

    def test_erro_400_nao_faz_retry(self):
        import urllib.error
        from fastapi import HTTPException
        from main import _extrair_campos_faltantes_gemini

        chamadas = {"n": 0}
        def mock_req(*args, **kwargs):
            chamadas["n"] += 1
            raise urllib.error.HTTPError(url="", code=400, msg="bad request", hdrs=None, fp=None)  # type: ignore

        with patch("main._executar_requisicao_gemini_sincrona", side_effect=mock_req), \
             patch("main._gemini_api_key", "fake-key"):
            with self.assertRaises(HTTPException):
                self._run(
                    _extrair_campos_faltantes_gemini(
                        texto="x",
                        campos_extraidos={},
                        faltantes=["valor"],
                        max_tentativas=3,
                    )
                )
        self.assertEqual(chamadas["n"], 1)


from main import analisar_com_fallback


class AnalisarComFallbackMergeTest(unittest.TestCase):

    def _run(self, coro):
        return asyncio.run(coro)

    def test_fallback_gemini_e_usado_quando_confianca_baixa(self):
        """Verifica que quando o parser retorna confiança baixa, o fluxo Gemini é acionado
        e a ficha final contém os dados vindos da IA (mergeados)."""
        import json
        texto_pobre = "PROCESSO LICITATÓRIO. Contratação de serviços."

        resposta_ia = {
            "numero_edital": "PP 099/2026",
            "orgao": "Câmara Municipal de Curitiba",
            "cnpj": "76.530.547/0001-00",
            "modalidade": "Pregão Presencial",
            "objeto": "Contratação de serviços de limpeza",
            "valor": "R$ 80.000,00",
            "data_abertura": "20/08/2026 10:00",
            "prazo_envio_proposta": None,
            "prazo_vigencia": "12 meses",
            "criterio_julgamento": "Menor Preço",
            "documentos_habilitacao": ["Certidão negativa INSS"],
        }

        with patch("main.PARSER_FALLBACK_API", True), \
             patch("main._extrair_campos_faltantes_gemini", new_callable=AsyncMock, return_value=resposta_ia):
            ficha = self._run(analisar_com_fallback(texto_pobre, num_docs=1, modo="auto"))

        self.assertIn("## FICHA DE LICITAÇÃO", ficha)
        self.assertIn("PP 099/2026", ficha)
        self.assertIn("R$ 80.000,00", ficha)

    def test_fallback_cai_no_groq_quando_gemini_falha(self):
        """Quando _extrair_campos_faltantes_gemini lança HTTPException, deve chamar chamar_groq."""
        from fastapi import HTTPException as FastAPIHTTPException

        texto_pobre = "PROCESSO LICITATÓRIO. Contratação de serviços."

        ficha_groq_mock = "## FICHA DE LICITAÇÃO\n| Campo | Valor |\n|---|---|\n| **Nº / Processo** | 001 |"

        with patch("main.PARSER_FALLBACK_API", True), \
             patch("main._extrair_campos_faltantes_gemini",
                   new_callable=AsyncMock,
                   side_effect=FastAPIHTTPException(503, "Gemini falhou")), \
             patch("main.chamar_groq", new_callable=AsyncMock, return_value=ficha_groq_mock) as mock_groq:
            ficha = self._run(analisar_com_fallback(texto_pobre, num_docs=1, modo="auto"))

        mock_groq.assert_called_once()
        self.assertIn("## FICHA DE LICITAÇÃO", ficha)


if __name__ == "__main__":
    unittest.main()
