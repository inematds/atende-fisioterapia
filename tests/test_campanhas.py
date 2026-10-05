"""Seção 9: campanha só com consentimento e trava por conselho (fixture = COFFITO)."""
import pytest

from conftest import Servidor, com_conselho

CASOS = [
    # conselho, texto, violações esperadas (None = permitido)
    ("coffito", "Promoção de pilates clínico", {"promocao"}),
    ("coffito", "Sessão por apenas 80 reais", {"preco"}),
    ("coffito", "Avaliação postural grátis nesta semana", {"gratuito"}),
    ("coffito", "Resultado garantido em 5 sessões", {"promessa_resultado"}),
    ("coffito", "O melhor fisioterapeuta de Curitiba", {"melhor_profissional"}),
    ("coffito", "Veja o depoimento da nossa paciente", {"depoimento"}),
    ("coffito", "Novas turmas de pilates clínico às terças", None),
    ("cfm", "Consulta por R$ 300 nesta semana", None),
]


@pytest.mark.parametrize("conselho,texto,esperado", CASOS, ids=[f"{c[0]}-{i}" for i, c in enumerate(CASOS)])
def test_trava_por_conselho(dados, conselho, texto, esperado):
    com_conselho(dados, conselho)
    api = Servidor(dados).subir()
    api.paciente("Maria", "41999990001", marketing=True)
    st, r = api.post("/api/campanhas", {"texto": texto})
    if esperado is None:
        assert st == 200 and r["enviadas"] == 1, (st, r)
    else:
        assert st == 422, (st, r)
        assert set(r["violacoes"]) == esperado
        assert api.saida("campanha") == []


def test_publico_so_com_consentimento_e_sem_parar(api):
    api.paciente("Com", "41999990001", marketing=True)
    api.paciente("Sem", "41999990002", marketing=False)
    api.paciente("Parou", "41999990003", marketing=True)
    api.msg("41999990003", "parar")
    st, r = api.post("/api/campanhas", {"texto": "Novas turmas de pilates clínico às terças"})
    assert st == 200 and r["enviadas"] == 1
    assert [m["telefone"] for m in api.saida("campanha")] == ["+5541999990001"]
