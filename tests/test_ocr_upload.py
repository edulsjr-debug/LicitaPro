import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

import main


class OcrUploadTest(unittest.TestCase):
    def test_texto_precisa_ocr(self):
        self.assertTrue(main._texto_precisa_ocr(" "))
        self.assertTrue(main._texto_precisa_ocr("Texto muito curto"))
        self.assertFalse(main._texto_precisa_ocr("Este PDF tem texto suficiente para dispensar OCR. " * 5))

    @patch("main._ocr_pagina_pdf")
    @patch("main.pdfplumber.open")
    @patch("main.fitz.open")
    def test_extrair_texto_pdf_usando_ocr_quando_texto_vem_vazio(self, mock_fitz_open, mock_pdf_open, mock_ocr_pagina):
        fake_page = SimpleNamespace(
            extract_text=MagicMock(return_value=""),
            extract_words=MagicMock(return_value=[]),
        )
        fake_pdf = SimpleNamespace(pages=[fake_page])
        mock_pdf_open.return_value.__enter__.return_value = fake_pdf
        mock_pdf_open.return_value.__exit__.return_value = False
        mock_fitz_open.return_value = SimpleNamespace(close=lambda: None)
        mock_ocr_pagina.return_value = "texto ocr legivel"

        resultado = main._extrair_texto_pdf(b"pdf-bytes")

        self.assertEqual(resultado, "texto ocr legivel")
        mock_ocr_pagina.assert_called_once()

    @patch("main._ocr_pagina_pdf")
    @patch("main.pdfplumber.open")
    @patch("main.fitz.open")
    def test_extrair_texto_pdf_nao_dispara_ocr_com_texto_suficiente(self, mock_fitz_open, mock_pdf_open, mock_ocr_pagina):
        fake_page = SimpleNamespace(
            extract_text=MagicMock(return_value=("texto suficiente para nao usar ocr. " * 10)),
            extract_words=MagicMock(return_value=[]),
        )
        fake_pdf = SimpleNamespace(pages=[fake_page])
        mock_pdf_open.return_value.__enter__.return_value = fake_pdf
        mock_pdf_open.return_value.__exit__.return_value = False
        mock_fitz_open.return_value = SimpleNamespace(close=lambda: None)

        resultado = main._extrair_texto_pdf(b"pdf-bytes")

        self.assertIn("texto suficiente", resultado)
        mock_ocr_pagina.assert_not_called()


if __name__ == "__main__":
    unittest.main()
