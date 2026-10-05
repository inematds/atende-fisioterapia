# atende-fisioterapia

**🇧🇷 [Português](README.md) · 🇺🇸 [English](README.en.md) · 🇪🇸 [Español](README.es.md)**

[![Atende Fisioterapia](guia/assets/banner-en.jpg)](https://inematds.github.io/atende-fisioterapia/guia/en/)

## 📖 User guide

Landing page and step-by-step guide: **https://inematds.github.io/atende-fisioterapia/guia/en/** · [Português](https://inematds.github.io/atende-fisioterapia/guia/) · [Español](https://inematds.github.io/atende-fisioterapia/guia/es/)

Patient care for **a physical therapy clinic**, in Python 3 with only the standard library and SQLite: evaluation and session scheduling, automatic confirmation, waitlist, **treatment plan** (planned × completed sessions, dropout and re-evaluation alerts), **prescribed home exercises** with a library of 12 animated exercises (SVG; MP4 through HyperFrames for WhatsApp), an opt-in daily reminder, **adherence and pain** logging with a clinical alert, FAQ, human queue, emergency (192, the Brazilian emergency number), campaigns with the COFFITO guardrail (the Brazilian physical therapy council) and LGPD (the Brazilian data protection law) for health data, records, schedule management, backup, WhatsApp through the Evolution API, the team on Telegram, export to the Recovery Dashboard of Raio-X de Margem and delivery in Docker for a VPS.

**Status (05/10/2026): planned, not implemented.** What exists is the contract, 98 black-box acceptance tests, the decisions with default proposals, the map of Raio-X leaks and the long-run folder, ready for anyone to run the implementation in their own environment with an agent.

The full contract is in `docs/ESPECIFICACAO.md`. The patient chat is at `/`, the team page at `/equipe` and each exercise at `/exercicios/<id>`. The bot never gives clinical advice: it only explains what the physical therapist prescribed and hands everything else to the team.

Note: the docs, tests and the bot's chat commands are in Portuguese. LGPD, COFFITO and `192` are Brazilian; in another country the clinic must swap in its local privacy law, professional council and emergency number.

Sibling project (the mold): [`atende-clinica`](https://inematds.github.io/atende-clinica/guia/en/) (93/93 tests). The differences are summarized at the start of the specification. Business rules come from [Raio-X de Margem](https://inematds.github.io/raio-x-margem/guia/en/).

## Structure

```
docs/ESPECIFICACAO.md      frozen contract (sections 0–25)
docs/DECISOES-ABERTAS.md   default proposals + questions only the owner can answer
docs/MAPA-RAIO-X.md        Raio-X leak → system piece
docs/VALIDACAO.md          adversarial validation of the plan (9 problems found, 3 blocking)
tests/                     98 black-box tests (pytest) + fixtures/clinica.json
exemplos/clinica.json      example clinic (token TROQUE-ESTE-TOKEN; 12 exercises)
longrun/2026-10-05-fisio-v1/   goal, loop.env, prompts, congelar.sh, verificar-limites.sh, verificar-independente.py
FALHAS.md                  one line per failure (date, what broke, smallest fix, prompt|infra)
```

The implementation (`atende`, `src/`, `web/`, `tools/`, `Dockerfile`, `docker-compose.yml`, `.env.exemplo`) is produced by the long run described below.

## How to run it in your own environment

This section belongs to the project owner; the implementer adds their own (running locally, VPS deployment) without rewriting it.

**Prerequisites:** Python 3.10+ and `pytest` (`python3 -m pytest --version`); `git`; for the headless loop, the Codex CLI logged in through a subscription and `~/projetos/execucao-longa` (method, `tools/loop-longrun.sh`); for the final verification, Docker and, optionally, Chromium/Playwright and Node ≥ 22 + FFmpeg (HyperFrames).

1. **Answer the decisions** in `docs/DECISOES-ABERTAS.md` ("ok em tudo", all fine, counts). If you change anything marked ⚠, adjust `docs/ESPECIFICACAO.md` and `tests/` before step 2 and check `python3 -m pytest -q --collect-only | tail -1`.
2. **Freeze the contract:** clean `git status`, then `bash longrun/2026-10-05-fisio-v1/congelar.sh` (writes `hash-congelado.txt` with the hash of `tests/`, `pytest.ini`, the specification and the verifiers, and makes the commit).
3. **Run** by one of three paths:
   - **Headless loop (recommended):** `~/projetos/execucao-longa/tools/loop-longrun.sh longrun/2026-10-05-fisio-v1` — reads `loop.env` (Codex `gpt-6-astra`, 20 cycles × 30 min, 8 G, stagnation 3, `CODEX_ARGS` with `network_access=true` because the tests start a server on 127.0.0.1), reverts any cycle that touches a protected file and commits a checkpoint.
   - **`/goal` in Claude Code:** follow `longrun/2026-10-05-fisio-v1/prompt-goal-claude.md` (a new session opened in this folder).
   - **`/goal` in the Codex TUI:** `codex -c sandbox_workspace_write.network_access=true` in this folder and paste `longrun/2026-10-05-fisio-v1/prompt-goal-codex.md`.
4. **Follow along:** `tail -f longrun/2026-10-05-fisio-v1/loop.log` (headless) and the files `state.md`, `progress.md`, `failures.md`; `git log --oneline` shows the checkpoints. Done = `python3 -m pytest -q tests/` → **98 passed** and `bash longrun/2026-10-05-fisio-v1/verificar-limites.sh` → **LIMITES OK**. The loop stops on its own after stagnation (3 cycles with no progress) or at the cap.
5. **Independent verification (level 4), after "done":** `python3 longrun/2026-10-05-fisio-v1/verificar-independente.py` → `INDEPENDENTE OK`. It brings up a clinic it has never seen, looks for fixture values in the code, opens 3 SVGs in a Chromium to prove they move (and checks that the 12 have their own animations), renders an MP4 with HyperFrames and runs `docker build` + a healthcheck. Without Chromium/Playwright or without HyperFrames those stages come out as `PULADO` (skipped), never as OK; install them and run again if you want the full proof. Docker is mandatory. The snap Chromium works (frames are written inside the repo, because the snap cannot see `/tmp`). The result of the plan's independent validation is in `docs/VALIDACAO.md`. Also open `/`, `/equipe` and `/exercicios/ponte` in the browser.
6. **Exercise MP4 videos** (a human step; needs network, Node ≥ 22, FFmpeg and Chromium): `python3 tools/render-exercicios` produces `web/exercicios/<id>.mp4` (4 s, 720×720, no audio) from each SVG — see section 25 of the specification. The MP4 files stay out of Git; on the VPS, run the command once or copy the files into the `EXERCICIOS_MP4_DIR` folder.
7. **Clinical review:** the 12 example exercises (steps, common mistakes, precautions, contraindications, "stop if") and the list of warning words in the specification (§6, rule 2) are a starting point — a physical therapist reviews them before use with a real patient.

Every real failure goes to `FALHAS.md` (one line: date, what broke, smallest fix, prompt|infra).
