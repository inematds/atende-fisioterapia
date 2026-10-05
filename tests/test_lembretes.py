"""Seções 7, 8 e 20: confirmação automática, resposta à confirmação, lista de espera, retorno após plano concluído."""
from conftest import Servidor, norm


def ag_por_id(api, data, ag_id):
    st, r = api.get(f"/api/agendamentos?data={data}")
    return next(a for a in r["agendamentos"] if a["id"] == ag_id)


def test_confirmacao_dentro_de_48h_uma_vez(api):
    p1 = api.paciente("Maria", "41999990001")
    p2 = api.paciente("José", "41999990002")
    _, a = api.agenda(p1, "2026-10-07T09:00", profissional="carla")   # 24 h depois de 06/10 09:00
    _, b = api.agenda(p2, "2026-10-09T09:00", profissional="carla")   # 72 h
    assert api.rodar()["enviadas"] == 1
    [m] = api.saida("confirmacao")
    assert m["agendamento_id"] == a["id"] and m["telefone"] == "+5541999990001" and m["paciente_id"] == p1
    t = norm(m["texto"])
    for trecho in ("sessao de fisioterapia", "07/10", "09:00", "1", "2"):
        assert trecho in t, trecho
    assert "r$" not in t
    assert api.rodar()["enviadas"] == 0
    assert api.rodar("2026-10-07T10:00")["enviadas"] == 1   # 09/10 09:00 − 07/10 10:00 = 47 h ≤ 48
    assert [x["agendamento_id"] for x in api.saida("confirmacao")] == [a["id"], b["id"]]


def test_responder_1_confirma_e_2_cancela(api):
    p1 = api.paciente("Maria", "41999990001")
    p2 = api.paciente("José", "41999990002")
    _, a = api.agenda(p1, "2026-10-07T09:00", profissional="carla")
    _, b = api.agenda(p2, "2026-10-07T10:00", profissional="carla")
    api.rodar()
    assert "confirmad" in norm(api.msg("41999990001", "1"))
    assert ag_por_id(api, "2026-10-07", a["id"])["status"] == "confirmado"
    assert "cancelad" in norm(api.msg("41999990002", "2"))
    assert ag_por_id(api, "2026-10-07", b["id"])["status"] == "cancelado"


def test_lista_de_espera_oferece_e_agenda(api):
    p1 = api.paciente("Maria", "41999990001")
    p2 = api.paciente("José", "41999990002")
    p3 = api.paciente("Rita", "41999990003")
    _, a = api.agenda(p1, "2026-10-07T09:00", profissional="carla")
    assert api.post("/api/espera", {"paciente_id": p2, "servico": "sessao", "data": "2026-10-07"})[0] == 201
    assert api.post("/api/espera", {"paciente_id": p3, "servico": "sessao", "data": "2026-10-07"})[0] == 201
    api.post(f"/api/agendamentos/{a['id']}/cancelar")
    ofertas = api.saida("espera")
    assert [m["telefone"] for m in ofertas] == ["+5541999990002"]
    assert "09:00" in ofertas[0]["texto"] and "1" in ofertas[0]["texto"]
    assert "agendad" in norm(api.msg("41999990002", "1"))
    st, r = api.get("/api/agendamentos?data=2026-10-07")
    ativos = [x for x in r["agendamentos"] if x["status"] != "cancelado"]
    assert [(x["paciente_id"], x["inicio"], x["profissional"]) for x in ativos] == [(p2, "2026-10-07T09:00", "carla")]


def test_espera_horario_ja_ocupado(api):
    p1 = api.paciente("Maria", "41999990001")
    p2 = api.paciente("José", "41999990002")
    p4 = api.paciente("Ana", "41999990004")
    _, a = api.agenda(p1, "2026-10-07T09:00", profissional="carla")
    api.post("/api/espera", {"paciente_id": p2, "servico": "sessao", "data": "2026-10-07"})
    api.post(f"/api/agendamentos/{a['id']}/cancelar")
    assert api.agenda(p4, "2026-10-07T09:00", profissional="carla")[0] == 201
    assert "ocupado" in norm(api.msg("41999990002", "1"))


def test_cancelar_pela_conversa_dispara_espera_so_do_mesmo_dia(api):
    p1 = api.paciente("Maria", "41999990001")
    p2 = api.paciente("José", "41999990002")
    p3 = api.paciente("Rita", "41999990003")
    api.agenda(p1, "2026-10-07T09:00", profissional="carla")
    api.post("/api/espera", {"paciente_id": p2, "servico": "sessao", "data": "2026-10-08"})  # outro dia
    api.post("/api/espera", {"paciente_id": p3, "servico": "sessao", "data": "2026-10-07"})
    api.rodar()
    api.msg("41999990001", "2")
    assert [m["telefone"] for m in api.saida("espera")] == ["+5541999990003"]


def test_retorno_apos_plano_concluido(api):
    p = api.paciente("Maria", "41999990001")
    plano = api.plano(p, servico="sessao", sessoes=1)
    _, a = api.agenda(p, "2026-10-07T09:00", servico="sessao", profissional="carla")
    api.presenca(a["id"], True)
    assert api.get(f"/api/planos/{plano['id']}")[1]["status"] == "concluido"
    # retorno = 07/10/2026 + 30 dias = 06/11/2026; aviso a partir de 06/11 − 7 = 30/10/2026
    assert api.rodar("2026-10-29T09:00")["enviadas"] == 0
    assert api.rodar("2026-10-30T09:00")["enviadas"] == 1
    [m] = api.saida("retorno")
    t = norm(m["texto"])
    assert m["telefone"] == "+5541999990001" and "reavalia" in t and "avaliacao fisioterapeutica" in t
    assert api.rodar("2026-10-31T09:00")["enviadas"] == 0


def test_plano_nao_concluido_nao_gera_retorno(api):
    p = api.paciente("Maria", "41999990001")
    api.plano(p, servico="sessao", sessoes=3)
    _, a = api.agenda(p, "2026-10-07T09:00", servico="sessao", profissional="carla")
    api.presenca(a["id"], True)
    assert api.rodar("2027-01-05T09:00")["enviadas"] == 0
    assert api.saida("retorno") == []


def test_confirmacao_sobrevive_a_reinicio(dados):
    s = Servidor(dados)
    api = s.subir()
    p = api.paciente("Maria", "41999990001")
    api.agenda(p, "2026-10-07T09:00", profissional="carla")
    assert api.rodar()["enviadas"] == 1
    s.parar()
    api2 = Servidor(dados).subir()
    assert api2.rodar()["enviadas"] == 0
    assert "confirmad" in norm(api2.msg("41999990001", "sim"))
