"""Seções 20 e 24: plano de tratamento, vínculo das sessões, alertas de abandono e reavaliação."""
from conftest import norm


def alertas(api):
    st, r = api.get("/api/alertas")
    assert st == 200, (st, r)
    return r["alertas"]


def test_criar_plano_e_contar_sessoes(api):
    pid = api.paciente()
    st, p = api.post("/api/planos", {"paciente_id": pid, "servico": "sessao", "sessoes_previstas": 6,
                                      "frequencia_semanal": 2, "profissional": "carla", "observacao": "lombalgia"})
    assert st == 201, p
    assert (p["status"], p["realizadas"], p["faltas"], p["faltas_seguidas"], p["restantes"]) == ("ativo", 0, 0, 0, 6)
    assert p["criado_em"] == "2026-10-06T09:00" and p["servico_avaliacao"] == "avaliacao" and p["ultima_sessao"] is None
    assert p["alerta_abandono"] is None and p["alerta_reavaliacao"] is None
    _, a = api.agenda(pid, "2026-10-07T09:00", "sessao", "carla", plano_id=p["id"])
    assert a["plano_id"] == p["id"]
    api.presenca(a["id"], True)
    _, b = api.agenda(pid, "2026-10-07T09:30", "sessao", "carla", plano_id=p["id"])
    api.presenca(b["id"], False)
    st, p2 = api.get(f"/api/planos/{p['id']}")
    assert (p2["realizadas"], p2["faltas"], p2["faltas_seguidas"], p2["restantes"]) == (1, 1, 1, 5)
    assert p2["ultima_sessao"] == "2026-10-07T09:00" and p2["status"] == "ativo"
    outro = api.paciente("Outro", "41999990002")
    q = api.plano(outro, servico="rpg", sessoes=3)
    assert [x["id"] for x in api.get("/api/planos")[1]["planos"]] == [p["id"], q["id"]]
    assert [x["id"] for x in api.get(f"/api/planos?paciente_id={pid}")[1]["planos"]] == [p["id"]]
    assert api.get("/api/planos/9999")[0] == 404


def test_vinculo_automatico_e_plano_errado_422(api):
    pid = api.paciente()
    p = api.plano(pid, servico="sessao", sessoes=4)
    st, a = api.agenda(pid, "2026-10-07T09:00", "sessao", "carla")
    assert st == 201 and a["plano_id"] == p["id"]                          # mesmo serviço: vincula sozinho
    st, b = api.agenda(pid, "2026-10-07T10:00", "avaliacao", "carla")
    assert st == 201 and b["plano_id"] is None                             # outro serviço: sem plano
    assert api.agenda(pid, "2026-10-07T11:00", "avaliacao", "carla", plano_id=p["id"])[0] == 422   # plano de outro serviço
    outro = api.paciente("Outro", "41999990002")
    assert api.agenda(outro, "2026-10-07T14:00", "sessao", "carla", plano_id=p["id"])[0] == 422    # plano de outro paciente
    assert api.get("/api/agendamentos?data=2026-10-07")[1]["agendamentos"][0]["plano_id"] == p["id"]


def test_validacoes_do_plano(api):
    pid = api.paciente()
    base = {"paciente_id": pid, "servico": "sessao", "sessoes_previstas": 10, "frequencia_semanal": 2}
    assert api.post("/api/planos", dict(base, paciente_id=9999))[0] == 404
    assert api.post("/api/planos", dict(base, servico="xyz"))[0] == 404
    assert api.post("/api/planos", dict(base, profissional="zz"))[0] == 404
    assert api.post("/api/planos", dict(base, sessoes_previstas=0))[0] == 422
    assert api.post("/api/planos", dict(base, frequencia_semanal="duas"))[0] == 422
    assert api.post("/api/planos", base)[0] == 201
    assert api.post("/api/planos", base)[0] == 409                      # já há plano ativo do mesmo serviço
    assert api.post("/api/planos", dict(base, servico="rpg"))[0] == 201  # outro serviço pode


def test_alerta_de_abandono_por_faltas_seguidas(api):
    pid = api.paciente("Maria", "41999990001")
    p = api.plano(pid, servico="sessao", sessoes=6)

    def sessao(inicio, compareceu):
        st, a = api.agenda(pid, inicio, "sessao", "carla")
        assert st == 201, a
        api.presenca(a["id"], compareceu)

    sessao("2026-10-07T09:00", False)
    assert api.rodar()["alertas"] == 0            # 1 falta < abandono_faltas (2)
    sessao("2026-10-07T09:30", False)
    assert api.rodar()["alertas"] == 1
    [al] = alertas(api)
    assert al["tipo"] == "abandono" and al["plano_id"] == p["id"] and al["paciente_id"] == pid and al["status"] == "aberto"
    assert "2 faltas seguidas" in al["texto"] and "sessao de fisioterapia" in norm(al["texto"]) and "Maria" in al["texto"]
    assert api.rodar()["alertas"] == 0            # idempotente
    assert api.get(f"/api/planos/{p['id']}")[1]["alerta_abandono"] is not None
    sessao("2026-10-08T09:00", True)              # zera a sequência
    assert api.get(f"/api/planos/{p['id']}")[1]["faltas_seguidas"] == 0
    sessao("2026-10-08T09:30", False)
    assert api.rodar()["alertas"] == 0
    sessao("2026-10-08T10:00", False)
    assert api.rodar()["alertas"] == 1            # nova sequência, novo alerta
    assert api.post(f"/api/alertas/{al['id']}/resolver")[1]["status"] == "resolvido"
    [novo] = alertas(api)                                       # só o da nova sequência fica aberto
    assert novo["id"] != al["id"] and novo["tipo"] == "abandono" and novo["plano_id"] == p["id"]
    assert api.post("/api/alertas/9999/resolver")[0] == 404


def test_alerta_de_reavaliacao_e_conclusao(api):
    pid = api.paciente("Maria", "41999990001")
    p = api.plano(pid, servico="sessao", sessoes=4)
    horas = iter(["09:00", "09:30", "10:00", "10:30"])

    def realizada():
        st, a = api.agenda(pid, f"2026-10-07T{next(horas)}", "sessao", "carla")
        assert st == 201, a
        api.presenca(a["id"], True)

    realizada()
    assert api.rodar()["alertas"] == 0            # restantes 3 > 2
    realizada()
    assert api.rodar()["alertas"] == 1            # restantes 2 ≤ reavaliacao_sessoes
    [al] = alertas(api)
    assert al["tipo"] == "reavaliacao" and "faltam 2" in al["texto"] and "reavalia" in norm(al["texto"])
    realizada()
    assert api.rodar()["alertas"] == 0            # um por plano
    realizada()
    st, p2 = api.get(f"/api/planos/{p['id']}")
    assert p2["status"] == "concluido" and p2["realizadas"] == 4 and p2["restantes"] == 0
    assert p2["ultima_sessao"] == "2026-10-07T10:30"
    assert api.rodar()["alertas"] == 0


def test_encerrar_plano(api):
    pid = api.paciente()
    p = api.plano(pid, servico="sessao", sessoes=10)
    st, r = api.post(f"/api/planos/{p['id']}/encerrar", {"motivo": "alta"})
    assert st == 200 and r["status"] == "encerrado"
    assert api.post(f"/api/planos/{p['id']}/encerrar", {"motivo": "alta"})[0] == 409
    assert api.agenda(pid, "2026-10-07T09:00", "sessao", "carla", plano_id=p["id"])[0] == 422
    st, a = api.agenda(pid, "2026-10-07T09:00", "sessao", "carla")
    assert st == 201 and a["plano_id"] is None
    assert api.post("/api/planos", {"paciente_id": pid, "servico": "sessao", "sessoes_previstas": 5, "frequencia_semanal": 1})[0] == 201
