# atende-fisioterapia

Atendimento ao paciente de **uma clínica de fisioterapia**, em Python 3 só com a biblioteca padrão e SQLite: agenda de avaliação e sessões, confirmação automática, lista de espera, **plano de tratamento** (sessões previstas × realizadas, alerta de abandono e de reavaliação), **exercícios domiciliares prescritos** com biblioteca de 12 exercícios animados (SVG; MP4 pelo HyperFrames para o WhatsApp), lembrete diário opt-in, registro de **adesão e dor** com alerta clínico, FAQ, fila humana, emergência (192), campanhas com trava do COFFITO e LGPD de dado de saúde, cadastros, gestão de agenda, backup, WhatsApp pela Evolution API, equipe pelo Telegram, exportação para o Painel de Recuperação do Raio-X de Margem e entrega em Docker para VPS.

O contrato completo está em `docs/ESPECIFICACAO.md`. O chat do paciente fica em `/`, a página da equipe em `/equipe` e cada exercício em `/exercicios/<id>`. O bot nunca dá orientação clínica: explica só o que o fisioterapeuta prescreveu e passa o resto para a equipe.

Projeto irmão (molde): [`atende-clinica`](../atende-clinica). Diferenças resumidas no início da especificação.

## Estrutura

```
docs/ESPECIFICACAO.md      contrato congelado (seções 0–25)
docs/DECISOES-ABERTAS.md   propostas padrão + perguntas que só o dono responde
docs/MAPA-RAIO-X.md        vazamento do Raio-X → peça do sistema
tests/                     98 testes caixa-preta (pytest) + fixtures/clinica.json
exemplos/clinica.json      clínica de exemplo (token TROQUE-ESTE-TOKEN; 12 exercícios)
longrun/2026-10-05-fisio-v1/   goal, loop.env, prompts, congelar.sh, verificar-limites.sh, verificar-independente.py
FALHAS.md                  uma linha por falha (data, o que quebrou, menor correção, prompt|infra)
```

A implementação (`atende`, `src/`, `web/`, `tools/`, `Dockerfile`, `docker-compose.yml`, `.env.exemplo`) é produzida pela execução longa descrita abaixo.

## Como rodar no seu ambiente

Esta seção é do dono do projeto; o implementador acrescenta as dele (Executar localmente, Deploy na VPS) sem reescrevê-la.

**Pré-requisitos:** Python 3.10+ e `pytest` (`python3 -m pytest --version`); `git`; para o loop headless, o Codex CLI logado pela assinatura e `~/projetos/execucao-longa` (método, `tools/loop-longrun.sh`); para a verificação final, Docker e, opcionalmente, Chromium/Playwright e Node ≥ 22 + FFmpeg (HyperFrames).

1. **Responder as decisões** em `docs/DECISOES-ABERTAS.md` (um "ok em tudo" vale). Se mudar algo marcado ⚠, ajuste `docs/ESPECIFICACAO.md` e `tests/` antes do passo 2 e confira `python3 -m pytest -q --collect-only | tail -1`.
2. **Congelar o contrato:** `git status` limpo, depois `bash longrun/2026-10-05-fisio-v1/congelar.sh` (grava `hash-congelado.txt` com o hash de `tests/`, `pytest.ini`, da spec e dos verificadores, e faz o commit).
3. **Executar** por um dos três caminhos:
   - **Loop headless (recomendado):** `~/projetos/execucao-longa/tools/loop-longrun.sh longrun/2026-10-05-fisio-v1` — lê `loop.env` (Codex `gpt-6-astra`, 20 ciclos × 30 min, 8 G, estagnação 3, `CODEX_ARGS` com `network_access=true` porque os testes sobem servidor em 127.0.0.1), reverte ciclo que toque arquivo protegido e faz o commit de checkpoint.
   - **`/goal` no Claude Code:** siga `longrun/2026-10-05-fisio-v1/prompt-goal-claude.md` (sessão nova aberta nesta pasta).
   - **`/goal` no Codex TUI:** `codex -c sandbox_workspace_write.network_access=true` nesta pasta e cole `longrun/2026-10-05-fisio-v1/prompt-goal-codex.md`.
4. **Acompanhar:** `tail -f longrun/2026-10-05-fisio-v1/loop.log` (headless) e os arquivos `state.md`, `progress.md`, `failures.md`; `git log --oneline` mostra os checkpoints. Critério de pronto: `python3 -m pytest -q tests/` → **98 passed** e `bash longrun/2026-10-05-fisio-v1/verificar-limites.sh` → **LIMITES OK**. O loop para sozinho por estagnação (3 ciclos sem avanço) ou teto.
5. **Verificação independente (nível 4), depois do "concluído":** `python3 longrun/2026-10-05-fisio-v1/verificar-independente.py` → `INDEPENDENTE OK`. Ela sobe uma clínica nunca vista, procura valores do fixture no código, abre 3 SVGs num Chromium para provar que se mexem (e confere que os 12 têm animações próprias), renderiza um MP4 pelo HyperFrames e faz `docker build` + healthcheck. Sem Chromium/Playwright ou sem HyperFrames, as etapas saem como `PULADO` (nunca como OK) — instale e rode de novo se quiser a prova completa; Docker é obrigatório. O Chromium do snap serve (os quadros são gravados dentro do repo, porque o snap não enxerga `/tmp`). Resultado da validação independente do plano: `docs/VALIDACAO.md`. Abra também `/`, `/equipe` e `/exercicios/ponte` no navegador.
6. **Vídeos MP4 dos exercícios** (passo humano; precisa de rede, Node ≥ 22, FFmpeg e Chromium): `python3 tools/render-exercicios` gera `web/exercicios/<id>.mp4` (4 s, 720×720, sem áudio) a partir de cada SVG — ver seção 25 da spec. Os MP4 não entram no Git; na VPS, rode o comando uma vez ou copie os arquivos para a pasta de `EXERCICIOS_MP4_DIR`.
7. **Revisão clínica:** os 12 exercícios do exemplo (passos, erros comuns, cuidados, contraindicações, "pare se") e a lista de palavras de alerta da spec (§6, regra 2) são um ponto de partida — um fisioterapeuta revisa antes de usar com paciente real.

Toda falha real vai para `FALHAS.md` (uma linha: data, o que quebrou, menor correção, prompt|infra).

## Deploy na VPS

(Seção escrita pelo implementador conforme a seção 19 da especificação: compose, proxy HTTPS, registro dos webhooks da Evolution e do Telegram com os segredos, backup diário no cron, endereço público e pasta dos vídeos.)
