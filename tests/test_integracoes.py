"""Seções 17 e 18: WhatsApp pela Evolution API (sendText e sendMedia) e equipe pelo Telegram (contra servidor falso local)."""
import json
import time
import urllib.error
import urllib.request

from conftest import CHAT_EQUIPE, PUBLIC_URL, SEGREDO_TG, SEGREDO_WH, Servidor, env_integracoes, esperar, norm

TEL = "41988887777"
NUM = "5541988887777"
ESTAC = "Temos convênio com o estacionamento ao lado (1 hora grátis)."

_ids = iter(range(1, 10 ** 6))


def evo(api, texto=None, numero=NUM, msg_id=None, from_me=False, sufixo="@s.whatsapp.net",
        evento="messages.upsert", message=None, segredo=SEGREDO_WH):
    if message is None:
        message = {"conversation": texto}
    corpo = {"event": evento, "instance": "clinica",
             "data": {"key": {"remoteJid": numero + sufixo, "fromMe": from_me, "id": msg_id or f"M{next(_ids)}"},
                      "pushName": "Paciente", "message": message, "messageType": "conversation"}}
    st, _ = api.post(f"/webhook/evolution/{segredo}", corpo, token=None)
    return st


def tg(api, texto, reply_to=None, chat=CHAT_EQUIPE, segredo=SEGREDO_TG):
    """Entrega um update do Telegram no webhook; devolve o status HTTP."""
    msg = {"message_id": next(_ids), "chat": {"id": chat}, "from": {"id": 7, "first_name": "Rita"}, "text": texto}
    if reply_to:
        msg["reply_to_message"] = {"message_id": reply_to}
    q = urllib.request.Request(api.base + "/webhook/telegram", method="POST",
                               data=json.dumps({"update_id": next(_ids), "message": msg}).encode(),
                               headers={"Content-Type": "application/json", "X-Telegram-Bot-Api-Secret-Token": segredo})
    try:
        with urllib.request.urlopen(q, timeout=10) as resp:
            return resp.status
    except urllib.error.HTTPError as e:
        return e.code


def textos_whats(externo):
    return [p["json"]["text"] for p in externo.whats()]


def textos_tg(externo):
    return [p["json"]["text"] for p in externo.telegram()]


def abre_atendimento(api, externo):
    api.msg(TEL, "quero falar com um atendente")
    assert esperar(lambda: len(externo.telegram()) >= 1)
    [at] = api.fila()
    abertura = next(p for p in externo.telegram() if f"#{at['id']}" in p["json"]["text"])
    return at, abertura


# --- WhatsApp (Evolution) ---------------------------------------------------------------

def test_whatsapp_responde_pela_evolution_e_ignora_o_que_nao_e_do_paciente(api_int, externo):
    assert evo(api_int, "tem estacionamento?", segredo="errado") == 404
    assert evo(api_int, "tem estacionamento?", msg_id="DUP1") == 200
    assert esperar(lambda: len(externo.whats()) == 1)
    [p] = externo.whats()
    assert p["json"]["number"] == NUM and p["json"]["text"] == ESTAC
    assert p["headers"].get("apikey") == "chave-evo"
    evo(api_int, "tem estacionamento?", msg_id="DUP1")                      # reenvio da Evolution
    evo(api_int, "tem estacionamento?", from_me=True)                        # mensagem da própria clínica
    evo(api_int, "tem estacionamento?", numero="1203630", sufixo="@g.us")   # grupo
    evo(api_int, "tem estacionamento?", evento="connection.update")
    time.sleep(0.8)
    assert textos_whats(externo) == [ESTAC]


def test_whatsapp_sem_texto(api_int, externo):
    evo(api_int, message={"audioMessage": {"seconds": 5}})
    assert esperar(lambda: textos_whats(externo) == ["Por enquanto só consigo ler mensagens de texto."])


def test_whatsapp_agenda_e_avisa_equipe(api_int, externo):
    def tem(trecho):
        return esperar(lambda: any(trecho in norm(t) for t in textos_whats(externo)))

    evo(api_int, "quero marcar uma consulta")
    assert tem("nome")
    evo(api_int, "João Souza")
    assert tem("1 - avaliacao fisioterapeutica")
    evo(api_int, "2")
    assert tem("2) 06/10 11:00 com diego lima")
    evo(api_int, "2")
    assert tem("agendad")
    [a] = api_int.get("/api/agendamentos?data=2026-10-06")[1]["agendamentos"]
    assert (a["telefone"], a["servico"], a["profissional"], a["inicio"]) == ("+" + NUM, "sessao", "diego", "2026-10-06T11:00")
    assert esperar(lambda: any("Novo agendamento: 06/10 11:00 João Souza — Sessão de fisioterapia com Diego Lima" in t
                               for t in textos_tg(externo)))
    assert all(str(p["json"]["chat_id"]) == str(CHAT_EQUIPE) for p in externo.telegram())


def test_saida_pela_evolution_com_reenvio(api_int, externo):
    pid = api_int.paciente("Maria", TEL)
    api_int.agenda(pid, "2026-10-07T09:00", profissional="carla")
    externo.falhas = 1
    r = api_int.rodar()
    assert r["enviadas"] == 1
    [m] = api_int.saida("confirmacao")
    assert m["status"] == "pendente"
    r = api_int.rodar()
    assert r["enviadas"] == 0 and r["reenviadas"] == 1
    assert api_int.saida("confirmacao")[0]["status"] == "enviado"
    [p] = externo.whats()
    assert p["json"]["number"] == NUM and "07/10" in p["json"]["text"]


def test_sem_evolution_status_simulado(api):
    pid = api.paciente("Maria", TEL)
    api.agenda(pid, "2026-10-07T09:00", profissional="carla")
    api.rodar()
    assert api.saida("confirmacao")[0]["status"] == "simulado"


def test_exercicio_com_mp4_vai_por_sendmedia(dados, externo, tmp_path):
    pasta = tmp_path / "mp4"
    pasta.mkdir()
    (pasta / "ponte.mp4").write_bytes(b"\x00\x00\x00\x18ftypmp42fake")
    api = Servidor(dados, env=env_integracoes(externo, EXERCICIOS_MP4_DIR=str(pasta))).subir()
    pid = api.paciente("Maria", TEL)
    api.prescricao(pid)
    assert esperar(lambda: any("LEMBRETE" in t for t in textos_whats(externo)))   # prescrição vai por texto
    evo(api, "como faço a ponte?")
    assert esperar(lambda: len(externo.media()) == 1)
    [p] = externo.media()
    j = p["json"]
    assert j["number"] == NUM and j["mediatype"] == "video" and j["media"] == PUBLIC_URL + "/exercicios/ponte.mp4"
    assert "Ponte" in j["caption"] and "1. Deite de costas" in j["caption"]
    assert p["headers"].get("apikey") == "chave-evo"
    assert not any("Deite de costas" in t for t in textos_whats(externo))
    assert any("Deite de costas" in m["texto"] for m in api.saida())


def test_exercicio_sem_mp4_vai_por_texto_com_link(dados, externo, tmp_path):
    vazia = tmp_path / "sem-mp4"
    vazia.mkdir()
    api_int = Servidor(dados, env=env_integracoes(externo, EXERCICIOS_MP4_DIR=str(vazia))).subir()
    pid = api_int.paciente("Maria", TEL)
    api_int.prescricao(pid)
    evo(api_int, "como faço a ponte?")
    assert esperar(lambda: any("1. Deite de costas" in t for t in textos_whats(externo)))
    t = next(t for t in textos_whats(externo) if "1. Deite de costas" in t)
    assert PUBLIC_URL + "/exercicios/ponte" in t
    assert externo.media() == []


# --- Telegram (equipe) ------------------------------------------------------------------

def test_abertura_vai_ao_grupo(api_int, externo):
    at, abertura = abre_atendimento(api_int, externo)
    t = abertura["json"]["text"]
    assert TEL in t.replace(" ", "").replace("-", "") and f"#{at['id']}" in t
    assert str(abertura["json"]["chat_id"]) == str(CHAT_EQUIPE)
    assert at["status"] == "aberto"


def test_emergencia_e_dor_forte_marcam_alta(api_int, externo):
    api_int.msg(TEL, "meu pai desmaiou aqui")
    assert esperar(lambda: any("ALTA" in t for t in textos_tg(externo)))
    pid = api_int.paciente("Maria", "41999990002")
    api_int.prescricao(pid)
    api_int.msg("41999990002", "dor 9")
    assert esperar(lambda: any("ALTA" in t and "dor 9" in t for t in textos_tg(externo)))
    api_int.msg("41999990003", "estou com dormência no braço")
    assert esperar(lambda: any("ALTA" in t and "dormência" in t for t in textos_tg(externo)))


def test_atendimento_aberto_silencia_bot_e_repassa(api_int, externo):
    at, abertura = abre_atendimento(api_int, externo)
    st, r = api_int.post("/api/mensagens", {"telefone": TEL, "texto": "tem estacionamento?"}, token=None)
    assert r["respostas"] == []
    assert esperar(lambda: any(p["json"].get("reply_to_message_id") == abertura["message_id"]
                               and "tem estacionamento" in p["json"]["text"] for p in externo.telegram()))
    # emergência e alerta clínico continuam respondendo
    assert "192" in api_int.msg(TEL, "agora estou com falta de ar")
    assert "192" in api_int.msg(TEL, "e a perna está dormente")


def test_equipe_responde_em_cima_da_mensagem(api_int, externo):
    at, abertura = abre_atendimento(api_int, externo)
    assert tg(api_int, "Olá, aqui é a Rita. Como posso ajudar?", reply_to=abertura["message_id"]) == 200
    assert esperar(lambda: any(m["texto"] == "Olá, aqui é a Rita. Como posso ajudar?" for m in api_int.saida("humano")))
    assert api_int.saida("humano")[0]["telefone"] == "+" + NUM
    assert esperar(lambda: "Olá, aqui é a Rita. Como posso ajudar?" in textos_whats(externo))


def test_webhook_telegram_protegido(api_int, externo):
    at, abertura = abre_atendimento(api_int, externo)
    assert tg(api_int, "invasor", reply_to=abertura["message_id"], segredo="errado") == 401
    assert tg(api_int, "outro grupo", reply_to=abertura["message_id"], chat=-1009999) == 200
    time.sleep(0.5)
    assert api_int.saida("humano") == []


def test_comandos_responder_encerrar_fila_e_rotas_da_equipe(api_int, externo):
    at, _ = abre_atendimento(api_int, externo)
    tg(api_int, f"/responder {at['id']} Já te ligo")
    assert esperar(lambda: [m["texto"] for m in api_int.saida("humano")] == ["Já te ligo"])
    n = len(externo.telegram())
    tg(api_int, "/fila")
    assert esperar(lambda: any(f"#{at['id']}" in t for t in textos_tg(externo)[n:]))
    tg(api_int, f"/encerrar {at['id']}")
    assert esperar(lambda: api_int.fila() == [])
    assert api_int.msg(TEL, "tem estacionamento?") == ESTAC
    at2, _ = abre_atendimento(api_int, externo)
    assert api_int.post(f"/api/atendimento-humano/{at2['id']}/responder", {"texto": "Pode vir às 10h"})[0] == 200
    assert [m["texto"] for m in api_int.saida("humano")] == ["Já te ligo", "Pode vir às 10h"]
    assert api_int.post(f"/api/atendimento-humano/{at2['id']}/encerrar")[0] == 200
    assert api_int.fila() == []


def test_comando_agenda(api_int, externo):
    pid = api_int.paciente("Maria Lima", "41999990001")
    api_int.agenda(pid, "2026-10-07T09:00", "sessao", "carla")
    api_int.agenda(pid, "2026-10-07T14:00", "avaliacao", "carla")
    _, c = api_int.agenda(pid, "2026-10-07T15:00", "sessao", "diego")
    api_int.post(f"/api/agendamentos/{c['id']}/cancelar")
    tg(api_int, "/agenda 2026-10-07")

    def achou():
        return any("09:00 Maria Lima — Sessão de fisioterapia (Carla Souza)" in t
                   and "14:00 Maria Lima — Avaliação fisioterapêutica (Carla Souza)" in t and "15:00" not in t
                   for t in textos_tg(externo))
    assert esperar(achou)


def test_alertas_vao_ao_grupo_e_comando_alertas(api_int, externo):
    pid = api_int.paciente("Maria Lima", "41999990001")
    api_int.plano(pid, servico="sessao", sessoes=6)
    for h in ("09:00", "09:30"):
        _, a = api_int.agenda(pid, f"2026-10-07T{h}", "sessao", "carla")
        api_int.presenca(a["id"], False)
    tg(api_int, "/alertas")
    assert esperar(lambda: "Nenhum alerta aberto." in textos_tg(externo))
    assert api_int.rodar()["alertas"] == 1
    [al] = api_int.get("/api/alertas")[1]["alertas"]
    assert esperar(lambda: any(t.startswith(f"Alerta abandono #{al['id']}:") and "Maria Lima" in t for t in textos_tg(externo)))
    n = len(externo.telegram())
    tg(api_int, "/alertas")
    assert esperar(lambda: any(f"#{al['id']} abandono Maria Lima" in t for t in textos_tg(externo)[n:]))


def test_cancelamento_pelo_chat_avisa_equipe(api_int, externo):
    pid = api_int.paciente("Maria", TEL)
    api_int.agenda(pid, "2026-10-07T09:00", profissional="carla")
    api_int.rodar()
    assert "cancelad" in norm(api_int.msg(TEL, "2"))
    assert esperar(lambda: any(t.startswith("Cancelado:") and "07/10 09:00" in t for t in textos_tg(externo)))
