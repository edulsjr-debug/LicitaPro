from unittest.mock import patch
import pytest
import email_service


@pytest.fixture(autouse=True)
def set_env(monkeypatch):
    monkeypatch.setenv("RESEND_API_KEY", "re_test_key")
    monkeypatch.setenv("NOTIFY_EMAIL", "notificacoes@example.com")


def test_send_analysis_complete_chama_resend():
    with patch("resend.Emails.send") as mock_send:
        mock_send.return_value = {"id": "mock-id"}
        email_service.send_analysis_complete(
            filename="edital-saude.pdf",
            score=78,
            analise_id="abc123",
        )

    mock_send.assert_called_once()
    payload = mock_send.call_args[0][0]
    assert payload["to"] == ["notificacoes@example.com"]
    assert "Score: 78" in payload["subject"]
    assert payload["from"] == "LicitaPRO <noreply@prumosaas.com.br>"


def test_score_e_filename_no_html():
    with patch("resend.Emails.send") as mock_send:
        mock_send.return_value = {"id": "mock-id"}
        email_service.send_analysis_complete(
            filename="pregao-obras.pdf",
            score=85,
            analise_id="xyz789",
        )

    html = mock_send.call_args[0][0]["html"]
    assert "85" in html
    assert "pregao-obras.pdf" in html


def test_nao_envia_quando_api_key_ausente(monkeypatch):
    monkeypatch.delenv("RESEND_API_KEY", raising=False)
    with patch("resend.Emails.send") as mock_send:
        email_service.send_analysis_complete("test.pdf", 50, "id1")
    mock_send.assert_not_called()


def test_nao_envia_quando_notify_email_ausente(monkeypatch):
    monkeypatch.delenv("NOTIFY_EMAIL", raising=False)
    with patch("resend.Emails.send") as mock_send:
        email_service.send_analysis_complete("test.pdf", 60, "id2")
    mock_send.assert_not_called()


def test_nao_lanca_excecao_quando_resend_falha():
    with patch("resend.Emails.send", side_effect=Exception("network error")):
        # deve retornar silenciosamente — nunca bloquear o pipeline
        email_service.send_analysis_complete("test.pdf", 45, "id3")
