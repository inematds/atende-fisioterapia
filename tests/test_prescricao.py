"""Seções 22 e 23: prescrição, lembrete diário (opt-in pelo chat), registro fiz/não fiz/dor, adesão semanal, dor forte.
Agora = ter 06/10/2026 09:00. Itens padrão do conftest: ponte seg/qua/sex, retração cervical ter/qui."""
from conftest import Servidor, norm

TEL = "41988887777"
TEL_N = "+5541988887777"


def adesao(api, pid, semanas=None):
    st, r = api.get(f"/api/pacientes/{pid}/adesao" + (f"?semanas={semanas}" if semanas else ""))
    assert st == 200, (st, r)
    return r


def test_criar_prescricao_envia_mensagem_e_substitui(api):
    pid = api.paciente("Maria", TEL)
    p = api.prescricao(pid)
    assert p["paciente_id"] == pid and p["inicio"] == "2026-10-06" and p["ativo"] is True
    assert p["lembrete_hora"] == "19:00" and p["lembrete_ativo"] is False
    assert [(i["exercicio"], i["nome"], i["dias"]) for i in p["itens"]] == \
        [("ponte", "Ponte", ["seg", "qua", "sex"]), ("retracao-cervical", "Retração cervical", ["ter", "qui"])]
    [m] = api.saida("prescricao")
    assert m["telefone"] == TEL_N and m["paciente_id"] == pid
    for trecho in ("Ponte", "3 x 10", "2x ao dia", "seg, qua, sex", "/exercicios/ponte", "Retração cervical", "LEMBRETE"):
        assert trecho in m["texto"], trecho
    assert api.get(f"/api/pacientes/{pid}/prescricao")[1]["id"] == p["id"]
    p2 = api.prescricao(pid, itens=[{"exercicio": "bird-dog", "series": 2, "repeticoes": 8, "vezes_dia": 1, "dias": ["sab"]}])
    assert p2["id"] != p["id"]
    assert [i["exercicio"] for i in api.get(f"/api/pacientes/{pid}/prescricao")[1]["itens"]] == ["bird-dog"]
    assert len(api.saida("prescricao")) == 2


def test_validacoes_da_prescricao(api):
    pid = api.paciente("Maria", TEL)
    item = {"exercicio": "ponte", "series": 3, "repeticoes": 10, "vezes_dia": 1, "dias": ["seg"]}
    rota = f"/api/pacientes/{pid}/prescricao"
    assert api.post("/api/pacientes/9999/prescricao", {"itens": [item]})[0] == 404
    assert api.post(rota, {"itens": []})[0] == 422
    assert api.post(rota, {"itens": [dict(item, exercicio="xyz")]})[0] == 422
    assert api.post(rota, {"itens": [dict(item, series=0)]})[0] == 422
    assert api.post(rota, {"itens": [dict(item, dias=[])]})[0] == 422
    assert api.post(rota, {"itens": [dict(item, dias=["segunda"])]})[0] == 422
    assert api.post(rota, {"itens": [item], "lembrete_hora": "25:99"})[0] == 422
    assert api.get(rota)[0] == 404
    assert api.post(rota, {"itens": [item], "lembrete_hora": "07:30"})[0] == 201
    assert api.get(rota)[1]["lembrete_hora"] == "07:30"
    assert api.delete(rota)[0] == 204
    assert api.get(rota)[0] == 404


def test_lembrete_opt_in_pelo_chat(api):
    pid = api.paciente("Maria", TEL)
    api.prescricao(pid)
    r = norm(api.msg(TEL, "lembrete 20:30"))
    assert "lembrete" in r and "20:30" in r
    p = api.get(f"/api/pacientes/{pid}/prescricao")[1]
    assert p["lembrete_ativo"] is True and p["lembrete_hora"] == "20:30"
    assert "lembrete" in norm(api.msg(TEL, "sem lembrete"))
    assert api.get(f"/api/pacientes/{pid}/prescricao")[1]["lembrete_ativo"] is False
    assert "19:00" in api.msg(TEL, "lembrete")                              # sozinho = lembrete_hora_padrao
    p = api.get(f"/api/pacientes/{pid}/prescricao")[1]
    assert p["lembrete_ativo"] is True and p["lembrete_hora"] == "19:00"
    st, r = api.put(f"/api/pacientes/{pid}/lembrete", {"lembrete_ativo": False})
    assert st == 200 and r["lembrete_ativo"] is False
    outro = api.paciente("Sem prescrição", "41900000008")
    assert "nao entendi" in norm(api.msg("41900000008", "lembrete 19:00"))


def test_lembrete_diario_no_horario_e_nos_dias(api):
    pid = api.paciente("Maria", TEL)
    api.prescricao(pid)
    api.msg(TEL, "lembrete 19:00")
    assert api.rodar("2026-10-06T18:59")["enviadas"] == 0
    assert api.rodar("2026-10-06T19:00")["enviadas"] == 1                # terça: só retração cervical
    [m] = api.saida("exercicio")
    assert m["paciente_id"] == pid and "Retração cervical" in m["texto"] and "2 x 10" in m["texto"]
    assert "FIZ" in m["texto"] and "Ponte" not in m["texto"]
    assert api.rodar("2026-10-06T19:30")["enviadas"] == 0                # uma por dia
    assert api.rodar("2026-10-07T19:00")["enviadas"] == 1                # quarta: ponte
    assert "Ponte" in api.saida("exercicio")[-1]["texto"]
    assert api.rodar("2026-10-10T19:00")["enviadas"] == 0                # sábado: nenhum item
    assert api.rodar("2026-10-11T19:00")["enviadas"] == 0                # domingo
    api.msg(TEL, "sem lembrete")
    assert api.rodar("2026-10-08T19:00")["enviadas"] == 0                # desligado


def test_registro_fiz_nao_fiz_e_dor_no_dia(api):
    pid = api.paciente("Maria", TEL)
    api.prescricao(pid)
    assert "registrad" in norm(api.msg(TEL, "fiz"))
    [reg] = adesao(api, pid)["registros"]
    assert (reg["data"], reg["fez"], reg["dor"]) == ("2026-10-06", True, None)
    assert "registrad" in norm(api.msg(TEL, "dor 3"))
    assert "registrad" in norm(api.msg(TEL, "não fiz tudo, dor 2"))
    [reg] = adesao(api, pid)["registros"]                                 # mesmo dia: atualiza, não duplica
    assert (reg["fez"], reg["dor"], reg["quando"]) == (False, 2, "2026-10-06T09:00")
    assert "nao entendi" in norm(api.msg(TEL, "fizemos a compra"))        # palavra inteira
    assert api.fila() == []
    # dor sem prescrição também registra; "fiz" sem prescrição não
    sem = api.paciente("Sem", "41900000008")
    assert "registrad" in norm(api.msg("41900000008", "dor 4"))
    assert [r["dor"] for r in adesao(api, sem)["registros"]] == [4]
    assert "nao entendi" in norm(api.msg("41900000008", "fiz"))


def test_dor_forte_abre_fila_alta_e_numero_puro_so_com_pendencia(api):
    pid = api.paciente("Maria", TEL)
    api.prescricao(pid)
    api.msg(TEL, "lembrete 19:00")
    api.rodar("2026-10-06T19:00")                                         # pendência: lembrete de exercício
    r = norm(api.msg(TEL, "8"))
    assert "registrad" in r and "fisioterapeuta" in r and "192" in r
    [f] = api.fila()
    assert f["prioridade"] == "alta" and f["telefone"] == TEL_N and "dor 8" in f["motivo"]
    assert [x["dor"] for x in adesao(api, pid)["registros"]] == [8]
    api.post(f"/api/atendimento-humano/{f['id']}/encerrar")
    outro = api.paciente("José", "41999990002")
    api.prescricao(outro)
    assert "nao entendi" in norm(api.msg("41999990002", "5"))             # sem pendência, número não é dor
    assert "registrad" in norm(api.msg("41999990002", "dor 6"))
    assert len(api.fila()) == 0                                           # 6 < dor_alerta (7)


def test_adesao_semanal(dados):
    # semana de 05/10 (seg) a 11/10 (dom); prescrição em 06/10 (ter); dias previstos até 09/10: 06, 07, 08, 09 = 4
    s = Servidor(dados)
    api = s.subir()
    pid = api.paciente("Maria", TEL)
    api.prescricao(pid)
    api.msg(TEL, "fiz, dor 3")
    s.parar()
    s = Servidor(dados, agora="2026-10-07T20:00")
    api = s.subir()
    api.msg(TEL, "não fiz")
    s.parar()
    s = Servidor(dados, agora="2026-10-08T20:00")
    api = s.subir()
    api.msg(TEL, "fiz")
    api.msg(TEL, "dor 5")
    s.parar()
    api = Servidor(dados, agora="2026-10-09T10:00").subir()
    r = adesao(api, pid)
    [sem] = r["semanas"]
    assert sem["inicio"] == "2026-10-05" and sem["previstos"] == 4 and sem["feitos"] == 2
    assert abs(sem["adesao_pct"] - 50.0) <= 0.06 and abs(sem["dor_media"] - 4.0) <= 0.06   # (3 + 5) / 2
    assert [(x["data"], x["fez"], x["dor"]) for x in r["registros"]] == \
        [("2026-10-06", True, 3), ("2026-10-07", False, None), ("2026-10-08", True, 5)]
    st, geral = api.get("/api/adesao")
    [p] = geral["pacientes"]
    assert (p["paciente_id"], p["nome"], p["ultima_dor"]) == (pid, "Maria", 5)
    assert abs(p["adesao_pct"] - 50.0) <= 0.06 and abs(p["dor_media"] - 4.0) <= 0.06


def test_prescricao_para_quem_parou_nao_envia(api):
    pid = api.paciente("Maria", TEL)
    api.msg(TEL, "parar")
    api.prescricao(pid)
    assert api.saida("prescricao") == []
    assert api.get(f"/api/pacientes/{pid}/prescricao")[0] == 200
