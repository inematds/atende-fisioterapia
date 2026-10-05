"""Seções 1, 4, 5 (saúde/serviços), 13 e persistência."""
from conftest import RAIZ, Servidor


def test_saude_traz_versao_do_arquivo(api):
    st, r = api.get("/api/saude", token=None)
    assert st == 200
    assert r["ok"] is True
    assert r["versao"] == (RAIZ / "VERSION").read_text().strip()


def test_servicos_na_ordem_da_config(api):
    st, r = api.get("/api/servicos", token=None)
    assert st == 200
    assert [s["id"] for s in r["servicos"]] == ["avaliacao", "sessao", "rpg"]
    assert r["servicos"][0]["duracao_min"] == 60 and r["servicos"][1]["duracao_min"] == 30


def test_rotas_da_equipe_exigem_token_e_publicas_nao(api):
    for metodo, rota in [("GET", "/api/saida"), ("GET", "/api/agendamentos?data=2026-10-07"),
                         ("POST", "/api/pacientes"), ("GET", "/api/atendimento-humano"),
                         ("GET", "/api/raiox?mes=2026-10"), ("POST", "/api/campanhas"),
                         ("GET", "/api/planos"), ("POST", "/api/planos"), ("GET", "/api/alertas"),
                         ("GET", "/api/adesao"), ("POST", "/api/exercicios")]:
        corpo = {} if metodo == "POST" else None
        assert api.req(metodo, rota, corpo, token=None)[0] == 401, rota
        assert api.req(metodo, rota, corpo, token="errado")[0] == 401, rota
    assert api.get("/api/horarios?servico=sessao&data=2026-10-07", token=None)[0] == 200
    assert api.get("/api/exercicios", token=None)[0] == 200
    assert api.post("/api/mensagens", {"telefone": "41911112222", "texto": "oi"}, token=None)[0] == 200


def test_paginas(api):
    st, html = api.get("/", token=None)
    assert st == 200 and 'id="chat"' in html
    st, html = api.get("/equipe", token=None)
    assert st == 200
    for el in ('id="agenda"', 'id="fila-humano"', 'id="saida"', 'id="pacientes"', 'id="planos"',
               'id="prescricoes"', 'id="adesao"', 'id="biblioteca"', 'id="alertas"'):
        assert el in html, el


def test_estado_persiste_ao_reiniciar(dados):
    s = Servidor(dados)
    api = s.subir()
    pid = api.paciente()
    st, ag = api.agenda(pid, "2026-10-07T09:00", profissional="carla")
    assert st == 201
    plano = api.plano(pid, sessoes=5)
    s.parar()
    s2 = Servidor(dados)
    api2 = s2.subir()
    st, r = api2.get("/api/agendamentos?data=2026-10-07")
    assert st == 200
    assert [a["id"] for a in r["agendamentos"]] == [ag["id"]]
    assert api2.agenda(pid, "2026-10-07T09:00", profissional="carla")[0] == 409
    assert api2.get(f"/api/planos/{plano['id']}")[1]["status"] == "ativo"


def test_cria_clinica_json_do_exemplo_se_faltar(tmp_path):
    d = tmp_path / "vazio"
    d.mkdir()
    api = Servidor(d).subir()
    assert api.get("/api/saude", token=None)[0] == 200
    assert (d / "clinica.json").exists()
    assert len(api.get("/api/exercicios", token=None)[1]["exercicios"]) >= 12
