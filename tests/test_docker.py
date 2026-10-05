"""Seção 19: entrega em Docker para a VPS (checagem estática; o build real fica no verificar-independente)."""
import re

from conftest import RAIZ

VARIAVEIS = ("EVOLUTION_URL", "EVOLUTION_API_KEY", "EVOLUTION_INSTANCIA", "WEBHOOK_SEGREDO", "PUBLIC_URL",
             "EXERCICIOS_MP4_DIR", "TELEGRAM_API_URL", "TELEGRAM_TOKEN", "TELEGRAM_CHAT_ID", "TELEGRAM_SEGREDO")


def ler(nome):
    p = RAIZ / nome
    assert p.exists(), f"falta {nome}"
    return p.read_text()


def test_dockerfile():
    d = ler("Dockerfile")
    assert re.search(r"^FROM\s+python:3", d, re.M)
    assert "pip install" not in d and "curl" not in d
    assert re.search(r"serve.*--host.*0\.0\.0\.0.*--porta.*8080.*--dados.*/dados", d.replace("\n", " ").replace('"', "").replace(",", " "))
    assert "HEALTHCHECK" in d and "/api/saude" in d
    assert re.search(r"^COPY\s+.*web/", d, re.M)


def test_compose():
    c = ler("docker-compose.yml")
    for trecho in ("atende:", "build: .", "unless-stopped", "env_file", ".env", "/dados", "127.0.0.1:8080:8080"):
        assert trecho in c, trecho


def test_env_exemplo_tem_todas_as_variaveis_sem_segredo_real():
    e = ler(".env.exemplo")
    for var in VARIAVEIS:
        assert re.search(rf"^{var}=\s*$", e, re.M), var          # presente e vazia
    assert "http" not in e
    assert not re.search(r"\d{8,10}:[A-Za-z0-9_-]{30,}", e)       # formato de token real do Telegram


def test_readme_explica_deploy_e_mantem_a_secao_do_dono():
    r = ler("README.md")
    assert "Como rodar no seu ambiente" in r
    # só o corpo da seção "## Deploy na VPS" (até o próximo "## "): a seção do dono já cita PUBLIC_URL etc.
    m = re.search(r"^##\s+Deploy na VPS\s*$(.*?)(?=^##\s|\Z)", r, re.M | re.S)
    assert m, "falta a seção '## Deploy na VPS' (seção 19)"
    deploy = m.group(1)
    for trecho in ("/webhook/evolution/", "MESSAGES_UPSERT", "setWebhook", "secret_token", "./atende backup",
                   "PUBLIC_URL", "EXERCICIOS_MP4_DIR", "render-exercicios"):
        assert trecho in deploy, trecho
