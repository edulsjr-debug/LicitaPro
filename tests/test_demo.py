"""Testes unitários dos helpers de demo (sem Supabase)."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))


def test_demo_get_ip_x_forwarded_for():
    """Prefere X-Forwarded-For ao client.host."""
    from unittest.mock import MagicMock
    import importlib
    import main as m

    req = MagicMock()
    req.headers = {"x-forwarded-for": "203.0.113.5, 10.0.0.1"}
    req.client.host = "127.0.0.1"
    assert m._demo_get_ip(req) == "203.0.113.5"


def test_demo_get_ip_fallback():
    """Usa client.host quando header ausente."""
    from unittest.mock import MagicMock
    import main as m

    req = MagicMock()
    req.headers = {}
    req.client.host = "192.168.1.1"
    assert m._demo_get_ip(req) == "192.168.1.1"


def test_demo_limite_estado_livre():
    """Estado com 0 usos deve permitir análise."""
    import main as m
    estado = {"usos": 0, "bonus_liberado": False}
    resultado = m._demo_calcular_estado(estado)
    assert resultado["permitido"] is True
    assert resultado["precisa_lead"] is False
    assert resultado["usos_restantes"] == 3


def test_demo_limite_estado_precisa_lead():
    """3 usos sem bônus deve exigir lead."""
    import main as m
    estado = {"usos": 3, "bonus_liberado": False}
    resultado = m._demo_calcular_estado(estado)
    assert resultado["permitido"] is False
    assert resultado["precisa_lead"] is True
    assert resultado["usos_restantes"] == 0


def test_demo_limite_estado_bonus_disponivel():
    """3 usos com lead_autorizado=True deve permitir bônus."""
    import main as m
    estado = {"usos": 3, "bonus_liberado": False}
    resultado = m._demo_calcular_estado(estado, lead_autorizado=True)
    assert resultado["permitido"] is True
    assert resultado["precisa_lead"] is False


def test_demo_limite_estado_bloqueado():
    """4+ usos bloqueia definitivamente."""
    import main as m
    estado = {"usos": 4, "bonus_liberado": True}
    resultado = m._demo_calcular_estado(estado)
    assert resultado["permitido"] is False
    assert resultado["precisa_lead"] is False
    assert resultado["bloqueado"] is True
