# Goal — fisio-v1

- **Início:** 2026-10-05 (planejado; a execução começa quando o dono rodar `congelar.sh`) · **Agente:** `codex exec` (gpt-6-astra, assinatura) em loop headless — `~/projetos/execucao-longa/tools/loop-longrun.sh` · alternativa: `/goal` no Codex TUI ou no Claude Code
- **Tetos:** 20 ciclos × 30 min (≤ 10 h) · memória 8G por ciclo · estagnação 3 ciclos

## Resultado
`./atende` sobe o atendimento de **uma clínica de fisioterapia** — agenda (avaliação e sessões), confirmação, lista de espera, plano de tratamento com alerta de abandono e de reavaliação, biblioteca de exercícios com 12 SVGs animados e páginas públicas, prescrição domiciliar com lembrete opt-in, registro de adesão e dor com alerta clínico, FAQ, fila humana, emergência, campanhas com trava COFFITO/LGPD, cadastros, gestão de agenda, backup, WhatsApp pela Evolution (texto e MP4), equipe pelo Telegram, exportação para o Painel do Raio-X e entrega em Docker —, conforme `docs/ESPECIFICACAO.md`.

## Especificação
**`docs/ESPECIFICACAO.md`** (contrato completo, congelado). Contexto: `docs/MAPA-RAIO-X.md`. Fora do escopo: seção 12 da especificação. O `tools/render-exercicios` (seção 25) é escrito pelo agente mas **não é executado** no loop (precisa de rede para o `npx`); quem o roda é o humano no nível 4.

## Critérios de pronto (verificáveis)

**Função**
- [ ] `python3 -m pytest -q tests/` → **98 passed**, 0 failed, 0 errors, 0 skipped

**Regressão**
- [ ] a mesma suíte inteira no teste final (o loop só fecha se todas passam juntas; teste que passava e voltou a falhar impede o fecho)
- [ ] `./atende serve` reiniciado com o mesmo `--dados` mantém o estado (coberto por `test_estado_persiste_ao_reiniciar`, `test_confirmacao_sobrevive_a_reinicio`, `test_semente_so_na_primeira_vez` e `test_adesao_semanal`, que reinicia 4 vezes com relógios diferentes)

**Limite**
- [ ] `bash longrun/2026-10-05-fisio-v1/verificar-limites.sh` → `LIMITES OK` (hash do contrato = `hash-congelado.txt`, nº de testes coletados = 98, só arquivos do escopo — `atende`, `src/`, `web/` (inclusive `web/exercicios/*.svg`), `tools/`, `exemplos/`, `README.md`, `VERSION`, `Dockerfile`, `docker-compose.yml`, `.env.exemplo`, `.dockerignore`, `.gitignore`, `CLAUDE.md`, `FALHAS.md`, esta pasta —, sem SDK/dependência externa, sem URL externa (o namespace `http://www.w3.org/` dos SVGs é a única exceção), sem chave de API, sem `0.0.0.0` no código)

**Teste rápido por ciclo**: `python3 -m pytest -q tests/`
**Teste completo no final**: `python3 -m pytest -q tests/ && bash longrun/2026-10-05-fisio-v1/verificar-limites.sh`

**Depois do "concluído" (humano, nível 4):** `python3 longrun/2026-10-05-fisio-v1/verificar-independente.py` → `INDEPENDENTE OK` (sem valores do fixture no código + clínica nunca vista com outros limiares + 3 SVGs se mexendo no Chromium + um MP4 renderizado pelo HyperFrames + `docker build` e healthcheck do container; as etapas de Chromium e HyperFrames podem sair como `pulado` quando a máquina não tem a ferramenta — nunca como OK), e abrir `/`, `/equipe` e `/exercicios/ponte` no navegador.

## Restrições
- só pela assinatura; nenhuma API, nenhuma rede externa, nenhuma dependência fora da biblioteca padrão do Python 3 (decisão 2 de `docs/DECISOES-ABERTAS.md`)
- não mexer em: `tests/`, `pytest.ini`, `docs/` (inclusive `ESPECIFICACAO.md`), `goal.md`, `hash-congelado.txt`, `congelar.sh`, `verificar-*.{sh,py}`, `loop.env`, `prompt.md`
- a seção **"Como rodar no seu ambiente"** do `README.md` é do dono: acrescentar as seções da spec (§19) sem reescrevê-la
- servidor só em `127.0.0.1`; ao testar à mão, porta 0 e matar só o PID que subiu
- não rodar `npx`, `npm`, `docker` nem nada que baixe pacote; `tools/render-exercicios` é escrito, não executado
- no loop headless não fazer commit (o loop faz); no /goal interativo, commit local a cada checkpoint; nunca criar repo remoto nem fazer push

## Portões humanos (parar e perguntar)
- teste que contradiz a especificação (registrar em `failures.md` com o trecho exato e parar — não "ajustar" o teste)
- qualquer chamada a API real (Evolution, Telegram, LLM, Pix) — durante a execução só os servidores falsos locais dos testes; dependência externa
- deploy na VPS, render dos MP4 (precisa de rede e Chromium) e revisão clínica dos 12 exercícios — são do humano
- mudança de contrato, criar repo, push, publicar
