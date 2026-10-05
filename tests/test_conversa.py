"""Seção 6: conversa — FAQ, não entendi, humano, emergência, alerta clínico, parar, agendamento pelo chat."""
from conftest import norm

TEL = "41988887777"
TEL_N = "+5541988887777"


def test_faq_responde_exatamente(api):
    assert api.msg(TEL, "Oi, vcs aceitam convenio?") == "Atendemos Unimed e particular."
    assert api.msg(TEL, "Onde fica a clínica de vocês?") == "Rua das Flores, 100, sala 5, Batel, Curitiba."
    assert api.msg(TEL, "tem estacionamento aí?") == "Temos convênio com o estacionamento ao lado (1 hora grátis)."


def test_nao_entendi_e_depois_passa_para_humano(api):
    r = norm(api.msg(TEL, "posso tomar ibuprofeno antes da sessão?"))
    assert "nao entendi" in r and "atendente" in r
    assert "ibuprofeno" not in r  # o bot não orienta remédio
    assert api.fila() == []
    api.msg(TEL, "e dipirona serve?")
    f = api.fila()
    assert len(f) == 1 and f[0]["telefone"] == TEL_N and f[0]["prioridade"] == "normal"


def test_pedido_de_atendente(api):
    assert "atendente" in norm(api.msg(TEL, "quero falar com um atendente"))
    f = api.fila()
    assert len(f) == 1 and f[0]["prioridade"] == "normal"


def test_emergencia(api):
    r = norm(api.msg(TEL, "Estou com DOR NO PEITO e falta de ar"))
    assert "192" in r and "pronto-socorro" in r
    f = api.fila()
    assert len(f) == 1 and f[0]["prioridade"] == "alta" and f[0]["telefone"] == TEL_N
    # emergência vence o agendamento
    assert "192" in norm(api.msg("41988880000", "quero marcar sessão, estou sangrando muito"))
    assert api.get("/api/agendamentos?data=2026-10-06")[1]["agendamentos"] == []


def test_alerta_clinico_por_palavra_inteira(api):
    api.paciente("Maria", TEL)
    r = norm(api.msg(TEL, "depois do exercício senti dormência na perna"))
    assert "fisioterapeuta" in r and "192" in r
    for proibido in ("tome", "alongue", "faca "):
        assert proibido not in r, proibido
    f = api.fila()
    assert len(f) == 1 and f[0]["prioridade"] == "alta" and f[0]["telefone"] == TEL_N
    # "caixa" contém "cai" mas não é palavra inteira de alerta (não abre fila); "febre" é
    api.msg("41988880001", "deixei na caixa de entrada")
    assert len(api.fila()) == 1
    assert "192" in norm(api.msg("41988880002", "estou com febre desde ontem"))
    assert [x["prioridade"] for x in api.fila()] == ["alta", "alta"]


def test_agendamento_pelo_chat_paciente_novo(api):
    assert "nome" in norm(api.msg(TEL, "quero marcar uma consulta"))
    r = api.msg(TEL, "João Souza")
    assert "1 - Avaliação fisioterapêutica" in r and "2 - Sessão de fisioterapia" in r and "3 - RPG" in r
    r = api.msg(TEL, "1")
    # avaliação 60 min a partir de 11:00: 11:00 carla, 11:00 diego, 14:00 carla (11:30 não cabe até 12:00)
    assert "1) 06/10 11:00 com Carla Souza" in r
    assert "2) 06/10 11:00 com Diego Lima" in r
    assert "3) 06/10 14:00 com Carla Souza" in r
    r = norm(api.msg(TEL, "2"))
    assert "agendad" in r and "06/10" in r and "11:00" in r
    st, lista = api.get("/api/agendamentos?data=2026-10-06")
    [a] = lista["agendamentos"]
    assert (a["telefone"], a["servico"], a["profissional"], a["inicio"], a["status"]) == \
        (TEL_N, "avaliacao", "diego", "2026-10-06T11:00", "agendado")
    st, d = api.get(f"/api/pacientes/{a['paciente_id']}/dados")
    assert d["paciente"]["nome"] == "João Souza"
    assert d["paciente"]["consentimento_marketing"] is False


def test_agendamento_pelo_chat_paciente_conhecido_opcao_invalida_e_plano(api):
    pid = api.paciente("Maria", TEL)
    plano = api.plano(pid, servico="sessao", sessoes=8)
    r = api.msg(TEL, "quero agendar")
    assert "1 - Avaliação fisioterapêutica" in r
    r = api.msg(TEL, "2")  # sessão 30 min: 11:00 carla, 11:00 diego, 11:30 carla
    assert "1) 06/10 11:00 com Carla Souza" in r and "3) 06/10 11:30 com Carla Souza" in r
    r = api.msg(TEL, "9")
    assert "1) 06/10 11:00 com Carla Souza" in r  # repete as opções
    assert "agendad" in norm(api.msg(TEL, "1"))
    [a] = api.get("/api/agendamentos?data=2026-10-06")[1]["agendamentos"]
    assert (a["servico"], a["profissional"], a["inicio"], a["plano_id"]) == ("sessao", "carla", "2026-10-06T11:00", plano["id"])


def test_chat_oferece_proximos_dias_quando_hoje_lota(api):
    pid = api.paciente("Ocupa", "41900000001")
    for prof in ("carla", "diego"):
        for h in ("11:00", "14:00", "15:00", "16:00", "17:00"):
            assert api.agenda(pid, f"2026-10-06T{h}", "avaliacao", prof)[0] == 201
    api.msg(TEL, "quero agendar")
    api.msg(TEL, "Pedro")
    r = api.msg(TEL, "1")
    # dia seguinte livre, grade de 30 min: 08:00 carla, 08:00 diego, 08:30 carla
    assert "1) 07/10 08:00 com Carla Souza" in r and "2) 07/10 08:00 com Diego Lima" in r and "3) 07/10 08:30 com Carla Souza" in r


def test_cancelar_sai_do_fluxo(api):
    api.paciente("Maria", TEL)
    api.msg(TEL, "quero agendar")
    api.msg(TEL, "cancelar")
    assert api.msg(TEL, "tem estacionamento") == "Temos convênio com o estacionamento ao lado (1 hora grátis)."


def test_parar_bloqueia_contato(api):
    pid = api.paciente("Maria", TEL)
    api.agenda(pid, "2026-10-07T09:00", profissional="carla")
    api.prescricao(pid)
    api.msg(TEL, "lembrete 19:00")
    assert "nao vai mais receber" in norm(api.msg(TEL, "PARAR"))
    r = api.rodar("2026-10-06T19:30")
    assert r["enviadas"] == 0
    assert [m["tipo"] for m in api.saida()] == ["prescricao"]  # só a prescrição, enviada antes do PARAR
    st, d = api.get(f"/api/pacientes/{pid}/dados")
    assert d["paciente"]["nao_contatar"] is True
