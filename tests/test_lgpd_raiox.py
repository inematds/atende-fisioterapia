"""Seções 10 e 11: direitos do titular (LGPD) e exportação para o Painel de Recuperação do Raio-X."""
import json
import subprocess

from conftest import RAIZ, Servidor, norm

# minutos disponíveis em out/2026: 21 dias úteis (22 seg–sex menos o feriado 12/10) × 480 + 5 sábados × 240 = 11280,
# × 2 profissionais = 22560 (conferido com python3: laço sobre os dias do mês)
DISPONIVEL_OUT = 22560


def test_dados_e_exclusao(api):
    tel = "41999990001"
    pid = api.paciente("Maria Silva", tel, marketing=True)
    plano = api.plano(pid, servico="sessao", sessoes=5)
    _, a = api.agenda(pid, "2026-10-07T09:00", profissional="carla")
    _, b = api.agenda(pid, "2026-10-08T09:00", profissional="carla")
    api.presenca(b["id"], True)
    api.prescricao(pid)
    api.msg(tel, "fiz, dor 2")
    api.msg(tel, "tem estacionamento")
    st, d = api.get(f"/api/pacientes/{pid}/dados")
    assert st == 200
    assert d["paciente"]["nome"] == "Maria Silva" and d["paciente"]["telefone"] == "+5541999990001"
    assert d["paciente"]["lembrete_ativo"] is False and d["paciente"]["lembrete_hora"] == "19:00"
    assert {x["id"] for x in d["agendamentos"]} == {a["id"], b["id"]}
    assert {"entrada", "saida"} <= {m["direcao"] for m in d["mensagens"]}
    assert any("estacionamento" in m["texto"] for m in d["mensagens"])
    assert [p["id"] for p in d["planos"]] == [plano["id"]] and d["planos"][0]["realizadas"] == 1
    assert [i["exercicio"] for i in d["prescricao"]["itens"]] == ["ponte", "retracao-cervical"]
    assert [(r["data"], r["fez"], r["dor"]) for r in d["registros"]] == [("2026-10-06", True, 2)]

    assert api.delete(f"/api/pacientes/{pid}")[0] == 204
    st, d = api.get(f"/api/pacientes/{pid}/dados")
    assert st == 200
    assert d["paciente"]["nome"] == "removido" and d["paciente"]["telefone"] is None
    status = {x["id"]: x["status"] for x in d["agendamentos"]}
    assert status == {a["id"]: "cancelado", b["id"]: "realizado"}
    assert d["mensagens"] and all(m["texto"] == "" for m in d["mensagens"])
    assert d["planos"][0]["status"] == "encerrado" and d["prescricao"] is None and d["registros"] == []
    st, r = api.get("/api/raiox?mes=2026-10")
    assert r["valores"]["atendimentos_mes"] == 1 and r["valores"]["orcamentos_mes"] == 1
    assert "nome" in norm(api.msg(tel, "quero agendar"))  # telefone virou desconhecido


def montar_mes(dados):
    """Setembro: dois planos de 1 sessão concluídos (sex 04/09 e sáb 05/09) → retornos em 04/10 e 05/10.
    Outubro: o cenário medido (agora = ter 06/10 09:00)."""
    s = Servidor(dados, agora="2026-09-01T09:00")  # terça
    api = s.subir()
    p6 = api.paciente("Seis", "41900000006")
    p7 = api.paciente("Sete", "41900000007")
    for pid, dia in ((p6, "2026-09-04"), (p7, "2026-09-05")):
        api.plano(pid, servico="sessao", sessoes=1)
        st, a = api.agenda(pid, f"{dia}T09:00", "sessao", "carla")
        assert st == 201, a
        api.presenca(a["id"], True)            # plano concluído → retorno em dia + 30 (04/10 e 05/10)
    s.parar()

    s = Servidor(dados)  # agora = 06/10/2026 09:00
    api = s.subir()
    p1, p2, p3, p4, p5 = (api.paciente(n, f"4190000000{i}") for i, n in enumerate(["Um", "Dois", "Tres", "Quatro", "Cinco"], 1))
    api.plano(p1, servico="sessao", sessoes=10)   # orçamento de outubro, aprovado (sessão realizada)
    api.plano(p4, servico="sessao", sessoes=10)   # orçamento de outubro, só agendado

    def marca(pid, inicio, servico, prof, compareceu=None):
        st, a = api.agenda(pid, inicio, servico, prof)
        assert st == 201, (inicio, a)
        if compareceu is not None:
            api.presenca(a["id"], compareceu)
        return a

    marca(p1, "2026-10-07T08:00", "avaliacao", "carla", True)   # 60 min, novo
    marca(p1, "2026-10-07T09:00", "sessao", "carla", True)      # 30 min, vinculado ao plano de p1
    marca(p2, "2026-10-07T08:00", "sessao", "diego", False)     # 30 min, falta
    marca(p3, "2026-10-08T08:00", "avaliacao", "diego", True)   # 60 min, novo
    marca(p4, "2026-10-08T08:00", "sessao", "carla")            # 30 min, agendado (ativo), vinculado ao plano de p4
    c = marca(p5, "2026-10-08T09:00", "sessao", "carla")        # cancelado: não conta
    api.post(f"/api/agendamentos/{c['id']}/cancelar")
    marca(p6, "2026-10-07T10:00", "avaliacao", "carla", True)   # 60 min, cumpre o retorno de 04/10 (avaliação)
    return s, api


def test_raiox_numeros_do_mes(dados):
    s, api = montar_mes(dados)
    st, r = api.get("/api/raiox?mes=2026-10")
    assert st == 200 and r["pacote"] == "clinica" and r["mes"] == "2026-10"
    v = r["valores"]
    assert v["atendimentos_mes"] == 4                           # p1 ×2, p3, p6
    assert v["falta_pct"] == 20.0                               # 1 falta ÷ (4 + 1)
    assert v["clientes_novos_mes"] == 2                         # p1 e p3 (p6 já tinha realizado em setembro)
    assert v["retorno_atual_pct"] == 50.0                       # p6 cumpriu (07/10 ∈ 04/10 ± 30), p7 não
    assert abs(v["ocupacao_pct"] - 270 / DISPONIVEL_OUT * 100) <= 0.06   # 60+30+30+60+30+60 minutos ativos
    assert abs(v["atendimentos_mes_recorrente"] - 4 / 3) <= 0.06          # 4 realizados ÷ 3 pacientes (p1, p3, p6)
    assert v["orcamentos_mes"] == 2                             # planos de p1 e p4 criados em outubro
    assert v["aprovacao_atual_pct"] == 50.0                     # só o de p1 tem sessão realizada
    st, setembro = api.get("/api/raiox?mes=2026-09")
    vs = setembro["valores"]
    assert vs["atendimentos_mes"] == 2 and vs["clientes_novos_mes"] == 2 and vs["falta_pct"] == 0
    assert vs["atendimentos_mes_recorrente"] == 1.0 and vs["orcamentos_mes"] == 2 and vs["aprovacao_atual_pct"] == 100.0


def test_cli_grava_mes_no_acompanhamento_do_painel(dados, tmp_path):
    s, _ = montar_mes(dados)
    s.parar()
    arq = tmp_path / "acompanhamento.json"
    arq.write_text(json.dumps({
        "tipo": "acompanhamento", "pacote": "clinica", "cliente": "Fisio Movimento",
        "base": {"data": "2026-09-01", "valores": {"falta_pct": 18, "ticket_medio": 250, "atendimentos_mes": 400}},
        "meses": [],
    }))
    cmd = [str(RAIZ / "atende"), "raiox", "--dados", str(dados), "--mes", "2026-10", "--acompanhamento", str(arq)]
    for _ in range(2):  # rodar duas vezes substitui o mês, não duplica
        assert subprocess.run(cmd, cwd=RAIZ, capture_output=True, timeout=30).returncode == 0
    acomp = json.loads(arq.read_text())
    assert acomp["tipo"] == "acompanhamento" and acomp["base"]["valores"]["falta_pct"] == 18
    [m] = acomp["meses"]
    assert m["mes"] == "2026-10" and m["obs"] == "atende-fisioterapia"
    assert m["valores"]["ticket_medio"] == 250          # mesclado da base
    assert m["valores"]["falta_pct"] == 20.0            # medido
    assert m["valores"]["atendimentos_mes"] == 4
    assert abs(m["valores"]["atendimentos_mes_recorrente"] - 4 / 3) <= 0.06
    assert m["valores"]["orcamentos_mes"] == 2 and m["valores"]["aprovacao_atual_pct"] == 50.0
