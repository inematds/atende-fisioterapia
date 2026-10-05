# CLAUDE.md — atende-fisioterapia

Sistema de atendimento ao paciente para uma clínica de fisioterapia: agenda, confirmação, lista de espera, plano de tratamento (abandono/reavaliação), exercícios prescritos com SVG animado e lembrete, adesão e dor, FAQ, fila humana, emergência, campanhas com trava COFFITO/LGPD e exportação para o Painel do Raio-X de Margem. Derivado do `~/projetos/atende-clinica`.

- Repo local (sem remoto ainda). Autor de commit: `inematds <inematds@gmail.com>` (config local).
- **Contrato:** `docs/ESPECIFICACAO.md` (o bloco "O que muda em relação ao atende-clinica" resume as diferenças). Testes caixa-preta em `tests/` (pytest sobe `./atende serve --porta 0`). Contrato e testes são **protegidos** durante a execução longa — só humano altera, e aí recongela o hash.
- Decisões pendentes: `docs/DECISOES-ABERTAS.md`. Relação com o Raio-X: `docs/MAPA-RAIO-X.md`.
- Execução longa: `longrun/2026-10-05-fisio-v1/` (método em `~/projetos/execucao-longa`). Passo a passo para rodar: `README.md`, seção "Como rodar no seu ambiente".
- `python3` (não existe `python` neste host). Sem dependência externa no v1.
- Nenhuma API (WhatsApp/Meta, LLM pago, Pix/PSP, OpenRouter, Groq) sem autorização explícita. Sem rede externa no código. `tools/render-exercicios` (HyperFrames via `npx`) é passo humano, fora do loop.
- O bot **nunca** dá orientação clínica; dor forte e sinais de alerta vão para humano com prioridade alta.
- Servidor de teste: só `127.0.0.1`, porta 0; matar só o PID que subiu.
- Versão em `VERSION` (semver do CLAUDE global: minor carrega o patch).

## Self-learning

When I correct you, or you catch yourself making a mistake: before continuing, add the lesson as a one-line rule under ## Lessons, so it never happens again.

## Lessons
- Toda data/valor esperado num teste tem a conta num comentário e foi conferido com `python3 -c` (dia da semana, soma de dias, minutos disponíveis).
- Chromium do snap (`/snap/bin/chromium`) não grava em `/tmp` (tmp privado): screenshot do verificador vai numa pasta dentro do repo. O `chrome-headless-shell` do Playwright não avança animação CSS com `--virtual-time-budget` (quadros iguais) — só o `chrome` completo. Medido em 05/10/2026. (05/10/2026)
