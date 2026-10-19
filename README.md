# atende-fisioterapia

**🇧🇷 [Português](README.md) · 🇺🇸 [English](README.en.md) · 🇪🇸 [Español](README.es.md)**

[![Atende Fisioterapia](guia/assets/banner.jpg)](https://inematds.github.io/atende-fisioterapia/guia/)

## 📖 Guia de uso

Landing e guia passo a passo (PT/EN/ES): **https://inematds.github.io/atende-fisioterapia/guia/** · [English](https://inematds.github.io/atende-fisioterapia/guia/en/) · [Español](https://inematds.github.io/atende-fisioterapia/guia/es/)

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

**Estado (19/10/2026): sistema implementado, versão 0.7.0.** `python3 -m pytest -q tests/` → **98 passed**; `bash longrun/2026-10-05-fisio-v1/verificar-limites.sh` → **LIMITES OK** na entrega; verificação independente → **INDEPENDENTE OK** (render MP4 pelo HyperFrames pulado). A implementação (`atende`, `src/`, `web/`, `tools/`, `Dockerfile`, `docker-compose.yml`, `.env.exemplo`) foi produzida pela execução longa descrita em "Como foi construído".

## Como rodar no seu ambiente

**Pré-requisitos:** Python 3.10+ (a aplicação só usa a biblioteca padrão) e `pytest` para os testes; `git`; Docker para o deploy na VPS; opcionalmente Node ≥ 22, FFmpeg e Chromium para os vídeos MP4.

1. **Conferir:** `python3 -m pytest -q tests/` → **98 passed**.
2. **Rodar local:** `./atende serve --porta 8080 --dados ./dados` (detalhes em "Executar localmente"). Abra `/`, `/equipe` e `/exercicios/ponte` no navegador.
3. **Personalizar:** ajuste `dados/clinica.json` (horários, profissionais, serviços, FAQ, exercícios) e troque o token. As 21 decisões de comportamento estão em `docs/DECISOES-ABERTAS.md` (aceitas como propostas padrão).
4. **Deploy:** siga "Deploy na VPS" abaixo, com as suas credenciais da Evolution/WhatsApp e do Telegram.
5. **Vídeos MP4 dos exercícios** (opcional, passo humano ainda não executado; precisa de rede, Node ≥ 22, FFmpeg e Chromium): `python3 tools/render-exercicios` gera `web/exercicios/<id>.mp4` (4 s, 720×720, sem áudio) a partir de cada SVG — ver seção 25 da spec. Os MP4 não entram no Git; na VPS, rode o comando uma vez ou copie os arquivos para a pasta de `EXERCICIOS_MP4_DIR`. Sem MP4, os SVG animados continuam funcionando na web.
6. **Revisão clínica:** os 12 exercícios do exemplo (passos, erros comuns, cuidados, contraindicações, "pare se") e a lista de palavras de alerta da spec (§6, regra 2) são um ponto de partida — um fisioterapeuta revisa antes de usar com paciente real.

## Como foi construído (método)

O sistema foi feito por execução longa, e o método continua no repositório para quem quiser refazer ou adaptar:

1. **Decisões respondidas** em `docs/DECISOES-ABERTAS.md` ("ok em tudo"). Para mudar algo marcado ⚠, ajuste `docs/ESPECIFICACAO.md` e `tests/` e confira `python3 -m pytest -q --collect-only | tail -1`.
2. **Contrato congelado:** `bash longrun/2026-10-05-fisio-v1/congelar.sh` gravou `hash-congelado.txt` com o hash de `tests/`, `pytest.ini`, da spec e dos verificadores (`381b6510e90832d5`).
3. **Execução:** loop headless `~/projetos/execucao-longa/tools/loop-longrun.sh longrun/2026-10-05-fisio-v1` — lê `loop.env` (Codex `gpt-6-astra` pela assinatura, 20 ciclos × 30 min, 8 G, estagnação 3, `CODEX_ARGS` com `network_access=true` porque os testes sobem servidor em 127.0.0.1); fechou em 7 ciclos. Alternativas: `/goal` no Claude Code (`longrun/2026-10-05-fisio-v1/prompt-goal-claude.md`) ou no Codex TUI (`codex -c sandbox_workspace_write.network_access=true` e `prompt-goal-codex.md`).
4. **Travas e acompanhamento:** `verificar-limites.sh` conferia hash, contagem de testes e escopo de arquivos (ele compara com o commit congelado, então mudanças posteriores de documentação, como o guia, aparecem como fora do escopo — é esperado). Acompanhamento: `longrun/2026-10-05-fisio-v1/loop.log`, `state.md`, `progress.md`, `failures.md` e os commits de checkpoint (`git log --oneline`).
5. **Verificação independente (nível 4):** `python3 longrun/2026-10-05-fisio-v1/verificar-independente.py` → `INDEPENDENTE OK`. Ela sobe uma clínica nunca vista, procura valores do fixture no código, abre 3 SVGs num Chromium para provar que se mexem (e confere que os 12 têm animações próprias), renderiza um MP4 pelo HyperFrames e faz `docker build` + healthcheck. Sem Chromium/Playwright ou sem HyperFrames, as etapas saem como `PULADO` (nunca como OK); nesta rodada o render MP4 saiu `PULADO` (HyperFrames não instalado). O Chromium do snap serve (os quadros são gravados dentro do repo, porque o snap não enxerga `/tmp`). Validação do plano antes da execução: `docs/VALIDACAO.md`.

Toda falha real vai para `FALHAS.md` (uma linha: data, o que quebrou, menor correção, prompt|infra).

## Deploy na VPS

Os comandos desta seção são passos do operador na VPS.

1. Copie `.env.exemplo` para `.env` e mantenha esse arquivo privado (`chmod 600 .env`). Crie `dados/` e `backups/`; copie `exemplos/clinica.json` para `dados/clinica.json`, ajuste a clínica e troque o token antes de iniciar. O compose persiste o banco e a configuração em `./dados`.
2. Preencha somente as integrações que deseja habilitar. Evolution usa `EVOLUTION_URL`, `EVOLUTION_API_KEY`, `EVOLUTION_INSTANCIA` e `WEBHOOK_SEGREDO`. Telegram usa `TELEGRAM_API_URL`, `TELEGRAM_TOKEN`, `TELEGRAM_CHAT_ID` e `TELEGRAM_SEGREDO`. Sem configuração, a saída é simulada. Não use `ATENDE_AGORA` em produção.
3. Execute `docker compose up -d --build`. Confira `docker compose ps` e `docker compose logs atende`. O HEALTHCHECK consulta `/api/saude` com Python. A publicação fica somente em `127.0.0.1:8080`; o processo dentro do container aceita conexões da rede do container.
4. Configure seu proxy reverso (Nginx ou Caddy) para encaminhar o domínio à porta local 8080, preservando caminho, corpo e headers, com certificado HTTPS. Defina `PUBLIC_URL` como a origem pública HTTPS, sem barra final. Acesse `/api/saude`, `/`, `/equipe` e `/exercicios/ponte`. Recrie o serviço após mudanças de ambiente: `docker compose up -d --force-recreate`.
5. Na configuração da instância Evolution, registre o destino formado por `PUBLIC_URL` + `/webhook/evolution/<segredo>` (substitua `<segredo>` pelo `WEBHOOK_SEGREDO`) e selecione o evento `MESSAGES_UPSERT`. A instância deve ser a mesma de `EVOLUTION_INSTANCIA`. Não exponha a chave no navegador.
6. Para o Telegram, o operador registra o webhook usando o método `setWebhook` na base `TELEGRAM_API_URL`, no caminho `/bot<TELEGRAM_TOKEN>/setWebhook`, com os campos `url` (formado por `PUBLIC_URL` + `/webhook/telegram`) e `secret_token` igual a `TELEGRAM_SEGREDO`. O proxy deve preservar `X-Telegram-Bot-Api-Secret-Token`. Use o grupo configurado em `TELEGRAM_CHAT_ID`; comandos disponíveis: `/fila`, `/agenda`, `/alertas`, `/responder` e `/encerrar`.

Para vídeos, o operador pode rodar `python3 tools/render-exercicios` fora do container (Node ≥ 22, FFmpeg, Chromium e rede) ou copiar MP4 já renderizados para `web/exercicios/`. O compose monta essa pasta em `/app/web/exercicios`, somente para leitura. Defina `EXERCICIOS_MP4_DIR=/app/web/exercicios` no `.env`; se usar outra pasta, ajuste também o volume. Os MP4 ficam fora do Git. Sem MP4 ou sem `PUBLIC_URL`, a explicação segue como texto com link.

Backup diário: crie `backups/`, restrinja seu acesso e acrescente no crontab do operador (troque `/caminho/atende-fisioterapia` pelo diretório instalado):

```cron
0 2 * * * cd /caminho/atende-fisioterapia && docker compose exec -T atende ./atende backup --dados /dados --saida /backups/clinica-$(date +\%F).zip >> backups/cron.log 2>&1
```

O backup inclui configuração e snapshot consistente do SQLite, mesmo com o servidor ligado. Copie os arquivos para armazenamento protegido fora da VPS e defina retenção conforme a política da clínica. Para restaurar, pare o serviço, restaure e reinicie:

```sh
docker compose stop atende
docker compose run --rm --no-deps atende ./atende restaurar --dados /dados --entrada /backups/clinica-AAAA-MM-DD.zip
docker compose up -d atende
```

Confirmações, lembretes, alertas e reenvios dependem de chamadas periódicas a `POST /api/tarefas/rodar` com `X-Token`; não existe agendador automático no servidor. Configure um agendador interno autenticado para essa rota. O token da equipe está em `dados/clinica.json`.

## Executar localmente

```sh
./atende serve --porta 8080 --dados ./dados
```

O servidor imprime `PORTA=8080` e escuta somente em `127.0.0.1` por padrão; `--porta 0` escolhe uma porta livre. Python 3 e biblioteca padrão são suficientes. Sem configuração prévia, `exemplos/clinica.json` é copiado para a pasta de dados; personalize-o e altere o token antes de uso real. Integrações são opcionais e lidas do ambiente do processo; `.env` é carregado pelo compose, não automaticamente pelo CLI.

Versão 0.7.0: página `/equipe` com agenda, cadastros, planos, prescrição, adesão/dor, biblioteca e alertas. O token fica apenas em memória nesta aba. `tools/render-exercicios` foi escrito conforme a seção 25; sua execução e a revisão visual/clínica são passos humanos. Use `--so ponte` para um exercício ou `--saida DIR` para escolher a pasta dos MP4.
