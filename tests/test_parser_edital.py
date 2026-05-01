import unittest

from parser_edital import analisar_sem_api


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

    def test_baixa_confianca_aciona_fallback(self):
        resultado = analisar_sem_api("Documento sem estrutura reconhecivel.", min_confianca=70)

        self.assertLess(resultado["confianca"], 70)
        self.assertTrue(resultado["usar_fallback_api"])
        self.assertIn("Confiança baixa", resultado["ficha"])


if __name__ == "__main__":
    unittest.main()
