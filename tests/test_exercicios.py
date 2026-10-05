"""Seção 21: biblioteca de exercícios, páginas, SVG animado, explicação pelo chat (regra 9 da seção 6)."""
import json
import re
import xml.etree.ElementTree as ET

from conftest import FIXTURE, IDS_OBRIGATORIOS, RAIZ, Servidor, env_integracoes, norm

TEL = "41988887777"


def test_catalogo_minimo_na_ordem_do_fixture(api):
    st, r = api.get("/api/exercicios", token=None)
    assert st == 200
    ex = r["exercicios"]
    ids = [e["id"] for e in ex]
    assert len(ids) >= 12 and ids[:12] == IDS_OBRIGATORIOS
    assert len({e["regiao"] for e in ex}) >= 6
    for e in ex[:12]:
        for campo in ("nome", "apelidos", "regiao", "passos", "erros_comuns", "cuidados", "contraindicacoes", "pare_se"):
            assert e[campo], (e["id"], campo)
        assert e["ativo"] is True and e["svg"] is True, e["id"]


def test_svg_de_cada_exercicio_do_fixture(api):
    ids = [e["id"] for e in json.loads(FIXTURE.read_text())["exercicios"]]
    assert len(ids) >= 12
    for i in ids:
        arq = RAIZ / "web" / "exercicios" / f"{i}.svg"
        assert arq.exists(), f"falta web/exercicios/{i}.svg"
        assert arq.stat().st_size <= 60 * 1024, (i, "maior que 60 KB")
        texto = arq.read_text(encoding="utf-8")
        raiz = ET.fromstring(texto)                                           # XML válido
        assert raiz.tag == "{http://www.w3.org/2000/svg}svg" and raiz.get("viewBox"), (i, "raiz/viewBox")
        titulo = raiz.find("{http://www.w3.org/2000/svg}title")
        assert titulo is not None and titulo.text and titulo.text.strip(), (i, "title")
        assert "@keyframes" in texto and re.search(r"animation(-name)?\s*:", texto), (i, "sem animação CSS")
        baixo = texto.lower()
        for proibido in ("<script", "<animate", "<set", "<image", "<foreignobject", "@import"):
            assert proibido not in baixo, (i, proibido)
        assert "http" not in baixo.replace("http://www.w3.org/", ""), (i, "http fora do namespace")
        for ref in re.findall(r"""(?:xlink:)?href\s*=\s*["']([^"']*)["']""", texto):
            assert ref.startswith("#"), (i, "href externo", ref)
        for u in re.findall(r"url\(\s*['\"]?([^'\")]*)", texto):
            assert u.startswith("#"), (i, "url() externo", u)
        for dur in re.findall(r"animation(?:-duration)?\s*:[^;]*?(\d+(?:\.\d+)?)(m?s)\b", texto):
            seg = float(dur[0]) / (1000 if dur[1] == "ms" else 1)
            assert seg in (1.0, 2.0, 4.0), (i, "duração fora de 1/2/4 s", dur)
        st, tipo, corpo = api.bruto(f"/exercicios/{i}.svg")
        assert st == 200 and tipo.startswith("image/svg+xml") and corpo == arq.read_bytes(), (i, st, tipo)


def test_pagina_do_exercicio(api):
    st, html = api.get("/exercicios/ponte", token=None)
    assert st == 200
    assert 'id="exercicio"' in html and "Ponte" in html and "/exercicios/ponte.svg" in html
    assert "Deite de costas" in html and "Dor aguda na lombar" in html and "Arquear demais" in html
    assert api.get("/exercicios/nao-existe", token=None)[0] == 404
    assert api.bruto("/exercicios/nao-existe.svg")[0] == 404


def test_biblioteca_crud(api):
    novo = {"id": "remada-elastico", "nome": "Remada com elástico", "apelidos": ["remada"], "regiao": "costas",
            "passos": ["Prenda o elástico à frente, na altura do peito.", "Puxe os cotovelos para trás, juntando as escápulas."],
            "pare_se": ["Dor aguda no ombro."]}
    assert api.post("/api/exercicios", novo)[0] == 201
    assert api.post("/api/exercicios", novo)[0] == 409
    assert api.post("/api/exercicios", dict(novo, id="sem-passos", passos=[]))[0] == 422
    assert api.post("/api/exercicios", dict(novo, id="Id Errado"))[0] == 422
    e = next(x for x in api.get("/api/exercicios", token=None)[1]["exercicios"] if x["id"] == "remada-elastico")
    assert e["svg"] is False and e["ativo"] is True
    assert api.get("/exercicios/remada-elastico", token=None)[0] == 200    # página existe mesmo sem SVG
    assert api.bruto("/exercicios/remada-elastico.svg")[0] == 404
    st, r = api.put("/api/exercicios/remada-elastico", {"regiao": "costas e ombros"})
    assert st == 200 and r["regiao"] == "costas e ombros"
    assert api.put("/api/exercicios/xyz", {"regiao": "x"})[0] == 404
    st, r = api.delete("/api/exercicios/remada-elastico")
    assert st == 200 and r["ativo"] is False
    assert api.get("/exercicios/remada-elastico", token=None)[0] == 404
    pid = api.paciente()
    st, r = api.post(f"/api/pacientes/{pid}/prescricao", {"itens": [
        {"exercicio": "remada-elastico", "series": 3, "repeticoes": 10, "vezes_dia": 1, "dias": ["seg"]}]})
    assert st == 422, r


def test_chat_explica_exercicio_prescrito(api):
    pid = api.paciente("Maria", TEL)
    api.prescricao(pid)   # ponte + retração cervical
    r = api.msg(TEL, "como faço a ponte?")
    assert "Ponte" in r and "1. Deite de costas" in r and "4. Segure 2 segundos" in r
    assert "pare se" in norm(r) and "dor aguda na lombar" in norm(r)
    assert "/exercicios/ponte" in r
    r = api.msg(TEL, "me mostra o queixo para dentro")
    assert "Retração cervical" in r and "1. Sente com as costas apoiadas" in r and "/exercicios/retracao-cervical" in r
    r = api.msg(TEL, "quais são meus exercícios?")
    assert "Ponte" in r and "/exercicios/ponte" in r and "Retração cervical" in r and "Deite de costas" not in r


def test_chat_exercicio_fora_da_prescricao_vai_para_o_fisio(api):
    pid = api.paciente("Maria", TEL)
    api.prescricao(pid, itens=[{"exercicio": "ponte", "series": 3, "repeticoes": 10, "vezes_dia": 1, "dias": ["seg"]}])
    r = api.msg(TEL, "como faço a prancha?")
    assert "fale com seu fisioterapeuta" in norm(r) and "atendente" in norm(r)
    assert "Apoie antebraços" not in r and "1." not in r
    r = api.msg("41900000009", "como faço a ponte")                       # telefone sem cadastro
    assert "fale com seu fisioterapeuta" in norm(r) and "Deite de costas" not in r
    sem = api.paciente("Sem prescrição", "41900000008")
    assert "fale com seu fisioterapeuta" in norm(api.msg("41900000008", "quais são meus exercícios"))
    assert api.get(f"/api/pacientes/{sem}/prescricao")[0] == 404


def test_mp4_servido_da_pasta_configurada(dados, tmp_path):
    pasta = tmp_path / "mp4"
    pasta.mkdir()
    (pasta / "ponte.mp4").write_bytes(b"\x00\x00\x00\x18ftypmp42fake")
    api = Servidor(dados, env={"EXERCICIOS_MP4_DIR": str(pasta)}).subir()
    st, tipo, corpo = api.bruto("/exercicios/ponte.mp4")
    assert st == 200 and tipo.startswith("video/mp4") and corpo == (pasta / "ponte.mp4").read_bytes()
    assert api.bruto("/exercicios/gato-camelo.mp4")[0] == 404
