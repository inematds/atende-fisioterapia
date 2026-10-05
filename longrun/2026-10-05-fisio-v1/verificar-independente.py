#!/usr/bin/env python3
"""Verificação independente (nível 4) — rodar DEPOIS que o loop disser concluído. O agente não vê este arquivo no prompt.

1. Procura valores do fixture copiados no código (atalho para passar nos testes).
2. Sobe o sistema com uma clínica NUNCA vista (outros serviços, passo de 20 min, outros limiares de abandono,
   reavaliação e dor, outros dias de prescrição, outro relógio) e confere regras que só passam se a lógica for geral.
   Tudo explícito: nenhum atalho do conftest além do Servidor.
3. Prova de movimento: 3 SVGs abertos num Chromium (Playwright ou binário) em dois instantes → quadros diferentes;
   e pelo menos 6 blocos <style> distintos entre os 12 SVGs do exemplo (movimento próprio, seção 21).
   Sem Chromium → "PULADO" (nunca OK).
4. MP4: se o HyperFrames estiver instalado, `tools/render-exercicios --so ponte` e conferência por ffprobe. Senão "PULADO".
5. `docker build` + healthcheck real do container (docker é pré-requisito: ausente = falha, não "pulado").
Saída: INDEPENDENTE OK (com as linhas "PULADO", se houver), ou a lista do que falhou.

Armadilhas medidas em 05/10/2026 nesta máquina: o chromium do snap NÃO grava em /tmp (tmp privado do snap) — os
quadros vão numa pasta dentro do repo; o chrome-headless-shell do Playwright NÃO avança a animação CSS com
--virtual-time-budget (quadros iguais) — só o `chrome` completo serve.
"""
import json
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile
import time
import unicodedata
import urllib.request

RAIZ = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ / "tests"))
from conftest import IDS_OBRIGATORIOS, Servidor  # noqa: E402

falhas, pulados = [], []
TOKEN = "token-reab-77"
TEL = "11987654321"


def confere(cond, msg):
    if not cond:
        falhas.append(msg)


def norm(s):
    return "".join(c for c in unicodedata.normalize("NFD", (s or "").lower()) if unicodedata.category(c) != "Mn")


# ---------------------------------------------------------------------------------------------------------------
# 1. valores fixos do fixture no código (nomes de exercícios vivem legitimamente em web/exercicios, por isso ficam fora)
def valores_do_fixture_no_codigo():
    alvo = [p for p in ("atende", "src", "web", "tools") if (RAIZ / p).exists()]
    for trecho in ("Unimed", "Rua das Flores", "segredo-teste", "Carla Souza", "Diego Lima", "2026-10-06",
                   "Movimento Teste", "41999990001", "fisio.exemplo", "41988887777"):
        r = subprocess.run(["grep", "-rnF", trecho, *alvo], cwd=RAIZ, capture_output=True, text=True)
        confere(r.stdout == "", f"valor do fixture no código: {trecho!r}")


# ---------------------------------------------------------------------------------------------------------------
# 2. clínica nunca vista
CFG = {
    "nome": "Reabilitar Centro de Fisioterapia", "conselho": "coffito", "token": TOKEN, "passo_min": 20,
    "antecedencia_min_horas": 1, "janela_dias": 7, "confirmacao_horas": 24, "retorno_aviso_dias": 3,
    "abandono_faltas": 1, "reavaliacao_sessoes": 1, "reavaliacao_dias": 15, "dor_alerta": 5, "lembrete_hora_padrao": "07:30",
    "feriados": ["2026-11-02"],
    "horarios": {d: [["07:00", "11:00"]] for d in ("seg", "ter", "qua", "qui", "sex")} | {"sab": [], "dom": []},
    "profissionais": [{"id": "mara", "nome": "Mara Teles", "servicos": ["aval", "fisio"]}],
    "servicos": [{"id": "aval", "nome": "Avaliação inicial", "duracao_min": 60},
                 {"id": "fisio", "nome": "Fisioterapia ortopédica", "duracao_min": 40}],
    "faq": [{"id": "cartao", "perguntas": ["aceitam cartão de crédito"], "resposta": "Sim, débito e crédito."}],
    "exercicios": [
        {"id": "ponte", "nome": "Ponte de glúteo", "apelidos": ["ponte"], "regiao": "quadril",
         "passos": ["Deite numa superfície firme com os joelhos dobrados.", "Suba o quadril contando até dois."],
         "erros_comuns": ["Subir com impulso."], "cuidados": ["Devagar."], "contraindicacoes": ["Dor lombar aguda."],
         "pare_se": ["Dor que desce para a perna."]},
        {"id": "remada-elastico", "nome": "Remada com elástico", "apelidos": ["remada"], "regiao": "costas",
         "passos": ["Prenda o elástico à frente.", "Puxe os cotovelos para trás."]},
    ],
}


def clinica_nunca_vista():
    with tempfile.TemporaryDirectory() as tmp:
        d = pathlib.Path(tmp)
        (d / "clinica.json").write_text(json.dumps(CFG, ensure_ascii=False))
        s = Servidor(d, agora="2026-11-03T06:00")  # terça (02/11 é segunda e feriado no cfg)
        try:
            api = s.subir()
        except BaseException as e:  # pytest.fail levanta Failed (BaseException); fora do pytest vira traceback
            s.parar()
            confere(False, f"servidor não subiu com a clínica nunca vista: {e}")
            return
        try:
            _checa_clinica(api)
        finally:
            s.parar()


def _checa_clinica(api):
    def req(metodo, rota, corpo=None, token=TOKEN):
        return api.req(metodo, rota, corpo, token=token)

    def msg(texto):
        st, r = req("POST", "/api/mensagens", {"telefone": TEL, "texto": texto}, token=None)
        return "\n".join(r.get("respostas", [])) if st == 200 else ""

    def rodar(agora):
        return req("POST", "/api/tarefas/rodar", {"agora": agora})[1]

    # grade de 20 min (07:00..10:20 para 40 min dentro de 07–11 = 11 horários), feriado novo, token do fixture
    st, r = req("GET", "/api/horarios?servico=fisio&data=2026-11-03", token=None)
    h = [x["inicio"][11:] for x in r.get("horarios", [])]
    confere(h[:2] == ["07:00", "07:20"] and h[-1] == "10:20" and len(h) == 11, f"grade de 20 min errada: {h}")
    confere(req("GET", "/api/horarios?servico=fisio&data=2026-11-02", token=None)[1].get("horarios") == [], "feriado novo ignorado")
    confere(req("GET", "/api/saida", token="segredo-teste")[0] == 401, "token do fixture aceito")

    st, r = req("POST", "/api/pacientes", {"nome": "Paciente Novo", "telefone": TEL})
    confere(st == 201, f"cadastro: {st} {r}")
    pid = r.get("id")

    # prescrição com outros dias, lembrete na hora padrão da clínica (07:30), registro e adesão
    st, r = req("POST", f"/api/pacientes/{pid}/prescricao", {"itens": [
        {"exercicio": "ponte", "series": 2, "repeticoes": 12, "vezes_dia": 1, "dias": ["ter", "qui"]}]})
    confere(st == 201 and r.get("lembrete_hora") == "07:30" and r.get("lembrete_ativo") is False, f"prescrição: {st} {r}")
    confere("07:30" in msg("lembrete"), "lembrete sozinho não usou lembrete_hora_padrao da clínica")
    confere(rodar("2026-11-03T07:29").get("enviadas") == 0, "lembrete antes da hora")
    confere(rodar("2026-11-03T07:30").get("enviadas") == 1, "lembrete não saiu na hora")
    ex = [m for m in req("GET", "/api/saida")[1].get("mensagens", []) if m.get("tipo") == "exercicio"]
    confere(len(ex) == 1 and "Ponte de glúteo" in ex[0]["texto"] and "2 x 12" in ex[0]["texto"], f"texto do lembrete: {ex}")
    confere("registrad" in norm(msg("fiz")), "fiz não registrado")
    r5 = norm(msg("dor 5"))
    confere("registrad" in r5 and "fisioterapeuta" in r5, f"dor 5 com dor_alerta 5 não alertou: {r5}")
    fila = req("GET", "/api/atendimento-humano")[1].get("fila", [])
    confere(len(fila) == 1 and fila[0]["prioridade"] == "alta", f"fila humana: {fila}")
    # semana de 02/11 (segunda); previstos = só 03/11 (ter, ≥ início e ≤ hoje); feitos 1 → 100 %; dor_media 5
    st, ad = req("GET", f"/api/pacientes/{pid}/adesao")
    sem = ad.get("semanas", [{}])[0] if ad.get("semanas") else {}
    confere(sem.get("inicio") == "2026-11-02" and sem.get("previstos") == 1 and sem.get("feitos") == 1
            and abs((sem.get("adesao_pct") or 0) - 100.0) <= 0.06 and abs((sem.get("dor_media") or 0) - 5.0) <= 0.06,
            f"adesão: {ad}")
    if fila:
        req("POST", f"/api/atendimento-humano/{fila[0]['id']}/encerrar")

    # explicação só do prescrito, com o texto desta clínica
    r = msg("como faço a ponte")
    confere("Deite numa superfície firme" in r and "/exercicios/ponte" in r, f"explicação da ponte: {r!r}")
    confere("fale com seu fisioterapeuta" in norm(msg("como faço a remada")), "exercício não prescrito explicado")
    st, html = req("GET", "/exercicios/ponte", token=None)
    confere(st == 200 and "Deite numa superfície firme" in html, "página do exercício não usa o catálogo da clínica")
    confere(req("GET", "/exercicios/ponte.svg", token=None)[0] == 200, "svg da ponte não servido")
    confere(req("GET", "/exercicios/remada-elastico.svg", token=None)[0] == 404, "svg inexistente não deu 404")
    confere(req("GET", "/exercicios/remada-elastico", token=None)[0] == 200, "página sem svg não deu 200")
    confere(msg("vocês aceitam cartão de crédito?") == "Sim, débito e crédito.", "FAQ novo não respondido")

    # agenda, plano com outros limiares (abandono 1, reavaliação 1, 15 dias), retorno pelo serviço de avaliação explícito
    st, a = req("POST", "/api/agendamentos", {"paciente_id": pid, "servico": "aval", "inicio": "2026-11-03T07:00", "profissional": "mara"})
    confere(st == 201, f"agendar aval 07:00 → {st} {a}")
    req("POST", f"/api/agendamentos/{a.get('id')}/presenca", {"compareceu": True})
    confere(req("POST", "/api/agendamentos", {"paciente_id": pid, "servico": "fisio", "inicio": "2026-11-03T07:20", "profissional": "mara"})[0] == 409,
            "sobreposição com passo 20 não detectada")
    st, plano = req("POST", "/api/planos", {"paciente_id": pid, "servico": "fisio", "sessoes_previstas": 2,
                                             "frequencia_semanal": 2, "servico_avaliacao": "aval"})
    confere(st == 201 and plano.get("servico_avaliacao") == "aval", f"plano: {st} {plano}")

    def sessao(inicio, compareceu):
        st, x = req("POST", "/api/agendamentos", {"paciente_id": pid, "servico": "fisio", "inicio": inicio, "profissional": "mara"})
        confere(st == 201 and x.get("plano_id") == plano.get("id"), f"sessão {inicio}: {st} {x}")
        req("POST", f"/api/agendamentos/{x.get('id')}/presenca", {"compareceu": compareceu})

    sessao("2026-11-03T08:00", False)
    r = rodar("2026-11-03T09:00")
    al = req("GET", "/api/alertas")[1].get("alertas", [])
    confere(r.get("alertas") == 1 and len(al) == 1 and al[0]["tipo"] == "abandono", f"abandono com 1 falta: {r} {al}")
    sessao("2026-11-03T08:40", True)
    r = rodar("2026-11-03T09:30")
    al = req("GET", "/api/alertas")[1].get("alertas", [])
    confere(r.get("alertas") == 1 and [x["tipo"] for x in al] == ["abandono", "reavaliacao"], f"reavaliação com restantes 1: {r} {al}")
    sessao("2026-11-03T09:20", True)
    confere(req("GET", f"/api/planos/{plano.get('id')}")[1].get("status") == "concluido", "plano não concluiu")
    # retorno = 03/11 + 15 = 18/11; aviso a partir de 18/11 − 3 = 15/11
    confere(rodar("2026-11-14T08:00").get("enviadas") == 0, "retorno cedo demais")
    confere(rodar("2026-11-15T08:00").get("enviadas") == 1, "retorno não avisado")
    ret = [m for m in req("GET", "/api/saida")[1].get("mensagens", []) if m.get("tipo") == "retorno"]
    confere(len(ret) == 1 and "reavalia" in norm(ret[0]["texto"]) and "avaliacao inicial" in norm(ret[0]["texto"]), f"texto do retorno: {ret}")

    st, r = req("POST", "/api/campanhas", {"texto": "Promoção: sessão por R$ 50"})
    confere(st == 422 and set(r.get("violacoes", [])) == {"promocao", "preco"}, f"trava COFFITO: {st} {r}")

    # nov/2026: 3 realizados (aval + 2 fisio), 1 falta → 25 %; 1 paciente novo; recorrente 3/1; 1 plano, aprovado;
    # retorno de 18/11 cumprido pela aval de 03/11 (∈ 18/11 ± 30 dias) → 100 %
    st, rx = req("GET", "/api/raiox?mes=2026-11")
    v = rx.get("valores", {})
    confere(v.get("atendimentos_mes") == 3 and v.get("falta_pct") == 25.0 and v.get("clientes_novos_mes") == 1, f"raiox básico: {v}")
    confere(abs((v.get("atendimentos_mes_recorrente") or 0) - 3.0) <= 0.06 and v.get("orcamentos_mes") == 1
            and v.get("aprovacao_atual_pct") == 100.0 and v.get("retorno_atual_pct") == 100.0, f"raiox fisio: {v}")


# ---------------------------------------------------------------------------------------------------------------
# 3. prova de movimento dos SVGs (dois quadros em tempos diferentes têm de diferir)
def quadros_playwright(svg):
    try:
        from playwright.sync_api import sync_playwright
    except Exception:
        return None
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page(viewport={"width": 400, "height": 400})
        pg.goto(svg.resolve().as_uri())
        pg.wait_for_timeout(100)
        a = pg.screenshot()
        pg.wait_for_timeout(1100)
        c = pg.screenshot()
        b.close()
    return a, c


def binario_chromium():
    for nome in ("chromium", "chromium-browser", "google-chrome", "google-chrome-stable"):
        exe = shutil.which(nome)
        if exe:
            return exe
    # Chrome completo baixado pelo Playwright. NÃO usar o chrome-headless-shell: não avança a animação (quadros iguais).
    for p in sorted(pathlib.Path.home().glob(".cache/ms-playwright/chromium-*/chrome-linux*/chrome")):
        if p.is_file():
            return str(p)
    return None


def quadros_chromium(svg, exe=None):
    exe = exe or binario_chromium()
    if not exe:
        return None
    saidas = []
    # pasta temporária DENTRO do repo: o chromium do snap não enxerga /tmp (tmp privado) e deixaria PNG vazio = falha falsa
    with tempfile.TemporaryDirectory(dir=RAIZ, prefix=".verif-svg-") as t:
        for i, orcamento in enumerate((100, 1600)):
            png = pathlib.Path(t) / f"q{i}.png"
            subprocess.run([exe, "--headless=new", "--disable-gpu", "--no-sandbox", f"--screenshot={png}",
                            "--window-size=400,400", f"--virtual-time-budget={orcamento}", svg.resolve().as_uri()],
                           capture_output=True, timeout=60)
            saidas.append(png.read_bytes() if png.exists() else b"")
    return tuple(saidas)


def prova_de_movimento():
    svgs = [RAIZ / "web" / "exercicios" / f"{i}.svg" for i in ("ponte", "gato-camelo", "bird-dog")]
    if not all(p.exists() for p in svgs):
        confere(False, "faltam SVGs para a prova de movimento (ponte, gato-camelo, bird-dog)")
        return
    for svg in svgs:
        q = quadros_playwright(svg) or quadros_chromium(svg)
        if q is None:
            pulados.append("movimento dos SVGs: pulado (sem Playwright nem Chromium nesta máquina)")
            break
        confere(bool(q[0]) and bool(q[1]), f"Chromium não gravou os dois quadros de {svg.name} ({binario_chromium()})")
        confere(q[0] != q[1], f"SVG não se mexe entre dois instantes: {svg.name}")


def animacoes_proprias():
    """Entre os 12 SVGs do exemplo, pelo menos 6 blocos <style> diferentes (seção 21: movimento próprio)."""
    estilos = set()
    for i in IDS_OBRIGATORIOS:
        p = RAIZ / "web" / "exercicios" / f"{i}.svg"
        if not p.exists():
            continue
        m = re.search(r"<style[^>]*>(.*?)</style>", p.read_text(encoding="utf-8", errors="replace"), re.S | re.I)
        if m:
            estilos.add(re.sub(r"\s+", " ", m.group(1)).strip())
    confere(len(estilos) >= 6, f"só {len(estilos)} bloco(s) <style> distinto(s) entre os 12 SVGs (mínimo 6, seção 21)")


# ---------------------------------------------------------------------------------------------------------------
# 4. MP4 pelo HyperFrames (só se instalado; precisa de rede na primeira vez e Chromium)
def render_mp4():
    if not shutil.which("npx"):
        pulados.append("render MP4: pulado (npx/Node não instalado)")
        return
    hf = subprocess.run(["npx", "--no-install", "hyperframes", "--version"], cwd=RAIZ, capture_output=True, text=True)
    if hf.returncode != 0:
        pulados.append("render MP4: pulado (HyperFrames não instalado: `npx --no-install hyperframes --version` falhou)")
        return
    if not (RAIZ / "tools" / "render-exercicios").exists():
        confere(False, "tools/render-exercicios não existe")
        return
    if not shutil.which("ffprobe"):
        confere(False, "ffprobe não encontrado (FFmpeg é pré-requisito do render, seção 25)")
        return
    with tempfile.TemporaryDirectory() as t:
        r = subprocess.run(["python3", "tools/render-exercicios", "--so", "ponte", "--saida", t], cwd=RAIZ,
                           capture_output=True, text=True, timeout=900)
        mp4 = pathlib.Path(t) / "ponte.mp4"
        confere(r.returncode == 0 and mp4.exists() and mp4.stat().st_size > 0, f"render falhou: {r.stdout[-300:]} {r.stderr[-300:]}")
        if mp4.exists():
            fp = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration:stream=width,height",
                                 "-of", "default=nw=1", str(mp4)], capture_output=True, text=True)
            info = dict(l.split("=", 1) for l in fp.stdout.splitlines() if "=" in l)
            dur = float(info.get("duration", 0))
            confere(3.9 <= dur <= 4.1 and info.get("width") == "720" and info.get("height") == "720", f"mp4 fora do esperado: {info}")


# ---------------------------------------------------------------------------------------------------------------
# 5. container de verdade (precisa de docker; baixa a imagem python na 1ª vez)
def container():
    if not shutil.which("docker"):
        confere(False, "docker não encontrado (pré-requisito da verificação final — instale ou rode numa máquina com Docker)")
        return
    b = subprocess.run(["docker", "build", "-q", "-t", "atende-fisioterapia-verif", "."], cwd=RAIZ, capture_output=True, text=True)
    confere(b.returncode == 0, f"docker build falhou: {b.stderr[-300:]}")
    if b.returncode != 0:
        return
    c = subprocess.run(["docker", "run", "-d", "--rm", "-p", "127.0.0.1::8080", "atende-fisioterapia-verif"],
                       capture_output=True, text=True)
    cid = c.stdout.strip()
    if not cid:
        confere(False, f"docker run falhou: {c.stderr[-300:]}")
        return
    try:
        porta = subprocess.run(["docker", "port", cid, "8080"], capture_output=True, text=True).stdout.split(":")[-1].strip()
        ok = False
        for _ in range(40):
            try:
                ok = urllib.request.urlopen(f"http://127.0.0.1:{porta}/api/saude", timeout=2).status == 200
                break
            except Exception:
                time.sleep(0.5)
        confere(ok, "container não respondeu /api/saude")
    finally:
        subprocess.run(["docker", "stop", cid], capture_output=True)


# ---------------------------------------------------------------------------------------------------------------
def main():
    valores_do_fixture_no_codigo()
    clinica_nunca_vista()
    prova_de_movimento()
    animacoes_proprias()
    render_mp4()
    container()
    for p in pulados:
        print("PULADO:", p)
    if falhas:
        print("INDEPENDENTE FALHOU:")
        for f in falhas:
            print(" -", f)
        return 1
    print("INDEPENDENTE OK" + (f" ({len(pulados)} etapa(s) pulada(s) — ver acima)" if pulados else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
