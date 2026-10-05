"""Seções 3 e 5: horários, agendamento, conflito, cancelamento, remarcação, presença, telefone.
Agora = ter 06/10/2026 09:00. Grade de 30 min; sessao 30 min (carla, diego); avaliacao e rpg 60 min (rpg só carla)."""
import threading


def horarios(api, servico, data, profissional=None):
    rota = f"/api/horarios?servico={servico}&data={data}"
    if profissional:
        rota += f"&profissional={profissional}"
    st, r = api.get(rota, token=None)
    assert st == 200, (st, r)
    return [(h["inicio"], h["profissional"]) for h in r["horarios"]]


def test_horarios_respeitam_antecedencia_e_ordem(api):
    # agora 09:00 + 2 h = 11:00: manhã 11:00 e 11:30; tarde 14:00..17:30 (8) → 10 por profissional
    h = horarios(api, "sessao", "2026-10-06")
    assert h[:3] == [("2026-10-06T11:00", "carla"), ("2026-10-06T11:00", "diego"), ("2026-10-06T11:30", "carla")]
    assert len(h) == 20


def test_horarios_de_60_min_cabem_na_janela_e_so_quem_faz(api):
    # rpg 60 min só carla: 11:00 (11:00+60 = 12:00 cabe), 11:30 não cabe; tarde 14:00..17:00 (7)
    h = horarios(api, "rpg", "2026-10-06")
    assert [i for i, _ in h] == ["2026-10-06T11:00"] + [f"2026-10-06T{x}" for x in
                                                         ("14:00", "14:30", "15:00", "15:30", "16:00", "16:30", "17:00")]
    assert {p for _, p in h} == {"carla"}
    # dia inteiro de avaliação (60) por profissional: 08:00..11:00 (7) + 14:00..17:00 (7) = 14
    h = horarios(api, "avaliacao", "2026-10-07", "carla")
    assert len(h) == 14 and h[0] == ("2026-10-07T08:00", "carla") and h[-1] == ("2026-10-07T17:00", "carla")
    assert ("2026-10-07T11:30", "carla") not in h


def test_sem_horario_em_feriado_domingo_e_sabado_reduzido(api):
    assert horarios(api, "sessao", "2026-10-12") == []          # feriado (segunda)
    assert horarios(api, "sessao", "2026-10-11") == []          # domingo
    assert len(horarios(api, "sessao", "2026-10-10")) == 16     # sábado 08:00..11:30 × 2 profissionais


def test_agendar_e_listar(api):
    pid = api.paciente()
    st, r = api.agenda(pid, "2026-10-07T09:00", servico="avaliacao", profissional="carla")
    assert st == 201
    assert r["status"] == "agendado" and r["inicio"] == "2026-10-07T09:00" and r["fim"] == "2026-10-07T10:00"
    assert r["plano_id"] is None
    st, lista = api.get("/api/agendamentos?data=2026-10-07")
    a = lista["agendamentos"][0]
    assert (a["paciente_id"], a["telefone"], a["servico"], a["profissional"]) == (pid, "+5541999990001", "avaliacao", "carla")
    assert ("2026-10-07T09:00", "carla") not in horarios(api, "sessao", "2026-10-07")
    assert ("2026-10-07T09:30", "carla") not in horarios(api, "sessao", "2026-10-07")


def test_invalidos_422_e_inexistentes_404(api):
    pid = api.paciente()
    for inicio, servico, prof in [
        ("2026-10-07T12:00", "sessao", "carla"),      # almoço
        ("2026-10-07T09:15", "sessao", "carla"),      # fora da grade
        ("2026-10-07T11:30", "avaliacao", "carla"),   # não cabe na janela
        ("2026-10-06T10:00", "sessao", "carla"),      # antes da antecedência
        ("2026-10-12T09:00", "sessao", "carla"),      # feriado
        ("2026-10-07T09:00", "rpg", "diego"),         # profissional não faz
    ]:
        assert api.agenda(pid, inicio, servico, prof)[0] == 422, (inicio, servico, prof)
    assert api.agenda(9999, "2026-10-07T09:00")[0] == 404
    assert api.agenda(pid, "2026-10-07T09:00", servico="xyz")[0] == 404
    assert api.get("/api/horarios?servico=xyz&data=2026-10-07", token=None)[0] == 404


def test_sobreposicao_409(api):
    pid = api.paciente()
    assert api.agenda(pid, "2026-10-07T09:00", "sessao", "carla")[0] == 201
    assert api.agenda(pid, "2026-10-07T08:30", "avaliacao", "carla")[0] == 409
    assert api.agenda(pid, "2026-10-07T09:00", "sessao", "diego")[0] == 201


def test_sem_profissional_pega_o_primeiro_livre(api):
    pid = api.paciente()
    st1, a1 = api.agenda(pid, "2026-10-07T09:00")
    st2, a2 = api.agenda(pid, "2026-10-07T09:00")
    st3, _ = api.agenda(pid, "2026-10-07T09:00")
    assert (st1, st2, st3) == (201, 201, 409)
    assert (a1["profissional"], a2["profissional"]) == ("carla", "diego")


def test_concorrencia_um_so_vence(api):
    pid = api.paciente()
    codigos = []

    def tenta():
        codigos.append(api.agenda(pid, "2026-10-08T10:00", "sessao", "carla")[0])

    ts = [threading.Thread(target=tenta) for _ in range(10)]
    [t.start() for t in ts]
    [t.join() for t in ts]
    assert sorted(codigos) == [201] + [409] * 9


def test_cancelar_libera(api):
    pid = api.paciente()
    _, a = api.agenda(pid, "2026-10-07T09:00", "sessao", "carla")
    st, r = api.post(f"/api/agendamentos/{a['id']}/cancelar")
    assert st == 200 and r["status"] == "cancelado"
    assert ("2026-10-07T09:00", "carla") in horarios(api, "sessao", "2026-10-07")
    assert api.agenda(pid, "2026-10-07T09:00", "sessao", "carla")[0] == 201


def test_remarcar(api):
    pid = api.paciente()
    _, a = api.agenda(pid, "2026-10-07T09:00", "sessao", "carla")
    api.agenda(pid, "2026-10-07T10:00", "sessao", "carla")
    assert api.post(f"/api/agendamentos/{a['id']}/remarcar", {"inicio": "2026-10-07T10:00"})[0] == 409
    assert api.post(f"/api/agendamentos/{a['id']}/remarcar", {"inicio": "2026-10-07T12:00"})[0] == 422
    st, r = api.post(f"/api/agendamentos/{a['id']}/remarcar", {"inicio": "2026-10-08T15:00"})
    assert st == 200 and r["id"] == a["id"] and r["inicio"] == "2026-10-08T15:00" and r["status"] == "agendado"
    assert ("2026-10-07T09:00", "carla") in horarios(api, "sessao", "2026-10-07")


def test_presenca(api):
    pid = api.paciente()
    _, a = api.agenda(pid, "2026-10-07T09:00", profissional="carla")
    _, b = api.agenda(pid, "2026-10-07T10:00", profissional="carla")
    assert api.presenca(a["id"], True)["status"] == "realizado"
    assert api.presenca(b["id"], False)["status"] == "falta"
    assert api.post(f"/api/agendamentos/{a['id']}/presenca", {"compareceu": False})[0] == 409  # já marcada
    # falta continua ocupando o horário (ativo)
    assert ("2026-10-07T10:00", "carla") not in horarios(api, "sessao", "2026-10-07")


def test_telefone_normalizado_e_duplicado(api):
    st, r = api.post("/api/pacientes", {"nome": "A", "telefone": "(41) 99999-0001"})
    assert st == 201
    st2, r2 = api.post("/api/pacientes", {"nome": "A", "telefone": "+55 41 99999 0001"})
    assert st2 == 200 and r2["id"] == r["id"]
    st3, r3 = api.post("/api/pacientes", {"nome": "B", "telefone": "41 3333-4444"})
    assert st3 == 201 and r3["id"] != r["id"]
    st, dados = api.get(f"/api/pacientes/{r3['id']}/dados")
    assert dados["paciente"]["telefone"] == "+554133334444"
    for ruim in ("123", "abc", "+55 41 9999"):
        assert api.post("/api/pacientes", {"nome": "C", "telefone": ruim})[0] == 400, ruim
