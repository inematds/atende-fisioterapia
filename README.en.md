# atende-fisioterapia

**🇧🇷 [Português](README.md) · 🇺🇸 [English](README.en.md) · 🇪🇸 [Español](README.es.md)**

[![Atende Fisioterapia](guia/assets/banner.jpg)](https://inematds.github.io/atende-fisioterapia/guia/)

## 📖 User guide

Landing page and step-by-step guide (PT/EN/ES): **https://inematds.github.io/atende-fisioterapia/guia/** · [English](https://inematds.github.io/atende-fisioterapia/guia/en/) · [Español](https://inematds.github.io/atende-fisioterapia/guia/es/)

Patient service for **a physiotherapy clinic**, in Python 3 using only the standard library and SQLite: evaluation and session scheduling, automatic confirmation, waiting list, **treatment plan** (planned × completed sessions, dropout and reassessment alerts), **prescribed home exercises** with a library of 12 animated exercises (SVG; MP4 via HyperFrames for WhatsApp), opt-in daily reminder, **adherence and pain** logging with clinical alert, FAQ, human queue, emergency (192), campaigns with the COFFITO lock and LGPD handling of health data, registrations, schedule management, backup, WhatsApp through the Evolution API, staff via Telegram, export to the Recovery Dashboard of the Margin X-Ray (Raio-X de Margem), and Docker delivery for a VPS.

The full contract is in `docs/ESPECIFICACAO.md`. The patient chat lives at `/`, the staff page at `/equipe`, and each exercise at `/exercicios/<id>`. The bot never gives clinical guidance: it only explains what the physiotherapist prescribed and hands everything else to the staff.

Sibling project (template): [`atende-clinica`](../atende-clinica). Differences are summarized at the beginning of the specification.

## Structure

```
docs/ESPECIFICACAO.md      frozen contract (sections 0–25)
docs/DECISOES-ABERTAS.md   default proposals + questions only the owner can answer
docs/MAPA-RAIO-X.md        Raio-X leak → system component
tests/                     98 black-box tests (pytest) + fixtures/clinica.json
exemplos/clinica.json      sample clinic (token TROQUE-ESTE-TOKEN; 12 exercises)
longrun/2026-10-05-fisio-v1/   goal, loop.env, prompts, congelar.sh, verificar-limites.sh, verificar-independente.py
FALHAS.md                  one line per failure (date, what broke, smallest fix, prompt|infra)
```

**Status (10/19/2026): system implemented, version 0.7.0.** `python3 -m pytest -q tests/` → **98 passed**; `bash longrun/2026-10-05-fisio-v1/verificar-limites.sh` → **LIMITES OK** at delivery; independent verification → **INDEPENDENTE OK** (MP4 render via HyperFrames skipped). The implementation (`atende`, `src/`, `web/`, `tools/`, `Dockerfile`, `docker-compose.yml`, `.env.exemplo`) was produced by the long-running execution described in "How it was built".

## How to run in your environment

**Prerequisites:** Python 3.10+ (the application only uses the standard library) and `pytest` for the tests; `git`; Docker for the VPS deploy; optionally Node ≥ 22, FFmpeg and Chromium for the MP4 videos.

1. **Check:** `python3 -m pytest -q tests/` → **98 passed**.
2. **Run locally:** `./atende serve --porta 8080 --dados ./dados` (details in "Running locally"). Open `/`, `/equipe` and `/exercicios/ponte` in the browser.
3. **Customize:** adjust `dados/clinica.json` (hours, professionals, services, FAQ, exercises) and change the token. The 21 behavior decisions are in `docs/DECISOES-ABERTAS.md` (accepted as default proposals).
4. **Deploy:** follow "VPS deploy" below, with your own Evolution/WhatsApp and Telegram credentials.
5. **Exercise MP4 videos** (optional, a human step not yet performed; needs network, Node ≥ 22, FFmpeg and Chromium): `python3 tools/render-exercicios` generates `web/exercicios/<id>.mp4` (4 s, 720×720, no audio) from each SVG — see section 25 of the spec. The MP4s are not committed to Git; on the VPS, run the command once or copy the files into the folder set by `EXERCICIOS_MP4_DIR`. Without MP4s, the animated SVGs keep working on the web.
6. **Clinical review:** the 12 sample exercises (steps, common mistakes, precautions, contraindications, "stop if") and the alert-word list in the spec (§6, rule 2) are a starting point — a physiotherapist reviews them before use with real patients.

## How it was built (method)

The system was built by a long-running execution, and the method remains in the repository for anyone who wants to redo or adapt it:

1. **Decisions answered** in `docs/DECISOES-ABERTAS.md` ("ok on everything"). To change anything marked ⚠, adjust `docs/ESPECIFICACAO.md` and `tests/` and check `python3 -m pytest -q --collect-only | tail -1`.
2. **Frozen contract:** `bash longrun/2026-10-05-fisio-v1/congelar.sh` wrote `hash-congelado.txt` with the hash of `tests/`, `pytest.ini`, the spec and the verifiers (`381b6510e90832d5`).
3. **Execution:** headless loop `~/projetos/execucao-longa/tools/loop-longrun.sh longrun/2026-10-05-fisio-v1` — reads `loop.env` (Codex `gpt-6-astra` via subscription, 20 cycles × 30 min, 8 G, stagnation 3, `CODEX_ARGS` with `network_access=true` because the tests start a server on 127.0.0.1); it finished in 7 cycles. Alternatives: `/goal` in Claude Code (`longrun/2026-10-05-fisio-v1/prompt-goal-claude.md`) or in the Codex TUI (`codex -c sandbox_workspace_write.network_access=true` and `prompt-goal-codex.md`).
4. **Locks and monitoring:** `verificar-limites.sh` checked the hash, test count and file scope (it compares against the frozen commit, so later documentation changes, such as the guide, show up as out of scope — this is expected). Monitoring: `longrun/2026-10-05-fisio-v1/loop.log`, `state.md`, `progress.md`, `failures.md` and the checkpoint commits (`git log --oneline`).
5. **Independent verification (level 4):** `python3 longrun/2026-10-05-fisio-v1/verificar-independente.py` → `INDEPENDENTE OK`. It starts a clinic it has never seen, searches the code for fixture values, opens 3 SVGs in Chromium to prove they move (and checks that all 12 have their own animations), renders an MP4 via HyperFrames, and runs `docker build` + healthcheck. Without Chromium/Playwright or without HyperFrames, the steps come out as `PULADO` (skipped — never as OK); in this round the MP4 render came out `PULADO` (HyperFrames not installed). The snap Chromium works (frames are written inside the repo, because snap cannot see `/tmp`). Plan validation before execution: `docs/VALIDACAO.md`.

Every real failure goes into `FALHAS.md` (one line: date, what broke, smallest fix, prompt|infra).

## VPS deploy

The commands in this section are operator steps on the VPS.

1. Copy `.env.exemplo` to `.env` and keep that file private (`chmod 600 .env`). Create `dados/` and `backups/`; copy `exemplos/clinica.json` to `dados/clinica.json`, adjust the clinic and change the token before starting. The compose file persists the database and configuration in `./dados`.
2. Fill in only the integrations you want to enable. Evolution uses `EVOLUTION_URL`, `EVOLUTION_API_KEY`, `EVOLUTION_INSTANCIA` and `WEBHOOK_SEGREDO`. Telegram uses `TELEGRAM_API_URL`, `TELEGRAM_TOKEN`, `TELEGRAM_CHAT_ID` and `TELEGRAM_SEGREDO`. Without configuration, output is simulated. Do not use `ATENDE_AGORA` in production.
3. Run `docker compose up -d --build`. Check `docker compose ps` and `docker compose logs atende`. The HEALTHCHECK queries `/api/saude` with Python. Publishing is only on `127.0.0.1:8080`; the process inside the container accepts connections from the container network.
4. Configure your reverse proxy (Nginx or Caddy) to forward the domain to local port 8080, preserving path, body and headers, with an HTTPS certificate. Set `PUBLIC_URL` to the public HTTPS origin, without a trailing slash. Visit `/api/saude`, `/`, `/equipe` and `/exercicios/ponte`. Recreate the service after environment changes: `docker compose up -d --force-recreate`.
5. In the Evolution instance configuration, register the destination formed by `PUBLIC_URL` + `/webhook/evolution/<segredo>` (replace `<segredo>` with `WEBHOOK_SEGREDO`) and select the `MESSAGES_UPSERT` event. The instance must be the same as `EVOLUTION_INSTANCIA`. Do not expose the key in the browser.
6. For Telegram, the operator registers the webhook using the `setWebhook` method on the `TELEGRAM_API_URL` base, at the path `/bot<TELEGRAM_TOKEN>/setWebhook`, with the fields `url` (formed by `PUBLIC_URL` + `/webhook/telegram`) and `secret_token` equal to `TELEGRAM_SEGREDO`. The proxy must preserve `X-Telegram-Bot-Api-Secret-Token`. Use the group configured in `TELEGRAM_CHAT_ID`; available commands: `/fila`, `/agenda`, `/alertas`, `/responder` and `/encerrar`.

For videos, the operator can run `python3 tools/render-exercicios` outside the container (Node ≥ 22, FFmpeg, Chromium and network) or copy already-rendered MP4s into `web/exercicios/`. The compose file mounts that folder at `/app/web/exercicios`, read-only. Set `EXERCICIOS_MP4_DIR=/app/web/exercicios` in `.env`; if you use another folder, adjust the volume too. The MP4s stay out of Git. Without MP4s or without `PUBLIC_URL`, the explanation falls back to text with a link.

Daily backup: create `backups/`, restrict its access and add to the operator's crontab (replace `/caminho/atende-fisioterapia` with the installed directory):

```cron
0 2 * * * cd /caminho/atende-fisioterapia && docker compose exec -T atende ./atende backup --dados /dados --saida /backups/clinica-$(date +\%F).zip >> backups/cron.log 2>&1
```

The backup includes the configuration and a consistent SQLite snapshot, even with the server running. Copy the files to protected storage outside the VPS and set retention according to the clinic's policy. To restore, stop the service, restore and restart:

```sh
docker compose stop atende
docker compose run --rm --no-deps atende ./atende restaurar --dados /dados --entrada /backups/clinica-AAAA-MM-DD.zip
docker compose up -d atende
```

Confirmations, reminders, alerts and resends depend on periodic calls to `POST /api/tarefas/rodar` with `X-Token`; there is no automatic scheduler on the server. Configure an authenticated internal scheduler for this route. The staff token is in `dados/clinica.json`.

## Running locally

```sh
./atende serve --porta 8080 --dados ./dados
```

The server prints `PORTA=8080` and listens only on `127.0.0.1` by default; `--porta 0` picks a free port. Python 3 and the standard library are enough. Without prior configuration, `exemplos/clinica.json` is copied into the data folder; customize it and change the token before real use. Integrations are optional and read from the process environment; `.env` is loaded by compose, not automatically by the CLI.

Version 0.7.0: `/equipe` page with schedule, registrations, plans, prescription, adherence/pain, library and alerts. The token is kept only in memory in this tab. `tools/render-exercicios` was written according to section 25; running it and the visual/clinical review are human steps. Use `--so ponte` for a single exercise or `--saida DIR` to choose the MP4 folder.
