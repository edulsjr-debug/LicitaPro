import unittest

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


if __name__ == "__main__":
    unittest.main()
