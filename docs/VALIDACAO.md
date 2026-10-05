# Validação adversarial — fisio-v1 (2026-10-05)

Validador independente, sem ter visto o planejamento. Base: commit `e470201` (planejador, 2 rodadas de revisão própria). Correções: `45fec11` + o commit deste arquivo. **98 testes antes e depois** (nenhum teste criado ou removido; `goal.md` não muda).

**Resultado:** 3 problemas que **bloqueavam** um implementador honesto (passaria pela spec e falharia no teste), 4 que **atrapalhavam** (ambiguidade ou falha falsa do verificador), 2 **cosméticos**. Tudo corrigido no projeto; 2 pontos ficaram para o dono (`DECISOES-ABERTAS.md` 20 ⚠ e 21).

| Gravidade | O quê | Onde corrigi |
|---|---|---|
| bloqueia | §6 regra 6 (`exercicio`): número puro ≥ `dor_alerta` sem fila alta/`fisioterapeuta`/`192` — `test_dor_forte_abre_fila_alta_e_numero_puro_so_com_pendencia` exige | spec regra 6 |
| bloqueia | §6 regra 8: `não fiz tudo, dor 2` contém `fiz` e `nao fiz` sem precedência — `test_registro_fiz_nao_fiz_e_dor_no_dia` espera `fez: false` | spec regra 8 |
| bloqueia | §7 + regra 6 `espera`: oferta não dizia que é o par (`inicio`, `profissional`) — `test_espera_horario_ja_ocupado` espera `ocupado` com Diego livre | spec §7 e regra 6 |
| atrapalha | `verificar-independente.py` falhava **falsamente** nesta máquina: chromium do snap não grava em `/tmp` → PNG vazio → "SVG não se mexe" (em vez de "pulado"); `chrome-headless-shell` dá quadros iguais; `docker`/`npx`/`ffprobe` ausentes ou `subir()` falhando = traceback | verificador reescrito (funções importáveis, pasta temporária no repo, só `chrome` completo, guardas) |
| atrapalha | "sem resposta" da pendência (regra 6) não definido; `sem lembrete` × `lembrete`, hora com 1 dígito e faixa (regra 7); stopwords do FAQ sem lista (regra 11); regras 1/2 com atendimento já aberto | spec §6 |
| atrapalha | §18 "última mensagem do paciente" — teste cobra `dormência` com acento (texto original); §22/§24 datas do lembrete e dos alertas = `agora` da rodada; §8 retorno comparado por data; §10 "mês anterior" do CLI | spec §8, §10, §18, §22, §24 |
| atrapalha | `test_readme_explica_deploy...` aceitava 3 trechos que a seção do dono já tem | teste lê só o corpo de `## Deploy na VPS`; §19 fixa o H2 |
| cosmético | regra 9: "normalizados" sem dizer que `Bird-dog` casa `bird dog`; §21 não dizia que `animation-delay` é livre nem que o 1º tempo do atalho é a duração | spec |
| cosmético | spec §21 não pedia movimento próprio verificável | ≥ 6 blocos `<style>` distintos entre os 12 (spec + verificador) |

## 1. Teste × especificação, item a item

Lidos os 12 arquivos de teste (98 testes) contra as seções 0–25. Para cada teste conferi: ordem de listagem, arredondamento, pontas inclusivas/exclusivas, desempate, código HTTP, texto literal exigido e contagem de mensagens.

| Arquivo | Testes | Situação |
|---|---|---|
| `test_basico.py` | 6 | OK (401 antes do corpo, páginas/ids, persistência, exemplo com ≥ 12 exercícios) |
| `test_agenda.py` | 11 | OK (grade, janela, feriado, 422 × 404 × 409, concorrência, remarcar, presença, telefone) |
| `test_conversa.py` | 10 | OK após correções (FAQ com lista fechada; `fiz`/`nao fiz`; alerta por palavra inteira; fluxo de agendamento) |
| `test_lembretes.py` | 8 | OK após correção da oferta de espera = par (`inicio`, `profissional`) |
| `test_planos.py` | 6 | OK (contadores, `faltas_seguidas`, alerta por sequência, reavaliação uma vez, conclusão, encerrar) |
| `test_prescricao.py` | 8 | OK após correções (número puro com efeitos da regra 8; precedência de `nao fiz`; adesão §23) |
| `test_exercicios.py` | 8 | OK (CRUD, páginas, SVG caixa-preta, explicação só do prescrito, MP4 da pasta configurada) |
| `test_integracoes.py` | 15 | OK após §18 "texto original" (sendText/sendMedia, reenvio, Telegram, `/alertas`, avisos) |
| `test_lgpd_raiox.py` | 3 | OK (contas abaixo) |
| `test_cadastros.py` | 9 | OK (profissional com horário próprio, serviços, pacientes, FAQ, bloqueios, período, semente, backup) |
| `test_campanhas.py` | 9 | OK (tabela COFFITO + código `depoimento`; `cfm` não trava preço) |
| `test_docker.py` | 4 | corrigido (README só na seção Deploy) |

Ambiguidades de resposta curta (número puro, `fiz`, `não fiz`, `dor N`): ordem de decisão agora é determinística — regra 5 (fluxo) → 6 (pendência: só `confirmacao`/`espera`/`exercicio`, por igualdade, com "sem resposta" definido) → 7 (`lembrete`) → 8 (`nao fiz` antes de `fiz`; `dor N` duas palavras) → 9 → … Sem pendência, `5` cai em "não entendi" (teste cobra). Palavras de alerta × frases comuns: `dor 3` e `melhorou a dor` não casam nada; `a dor caiu` casa `caiu` → falso alarme (decisão 20 ⚠ para o dono). Texto exigido literalmente (`192`, `pronto-socorro`, `fale com seu fisioterapeuta`, `Pare se:`, `1. …`, `Nenhum alerta aberto.`, `Alerta <tipo> #<id>: …`, `Novo agendamento: …`, `Cancelado:`, `LEMBRETE`, `FIZ`) está todo na spec.

SVG: cumprível à mão só com `@keyframes` (ver esqueleto da §21); regex de duração do teste aceita `animation: nome 2s ease -1s infinite` (1º tempo = duração); proibição de SMIL coerente em spec (§21), teste (`<animate`, `<set`), `verificar-limites.sh` (linha do grep nos SVGs) e `verificar-independente.py` (prova de movimento + estilos distintos). Caminho `sendMedia` × link: os testes criam um `.mp4` falso em `tmp_path` e passam `EXERCICIOS_MP4_DIR` + `PUBLIC_URL` por ambiente — sem MP4 no repo (`*.mp4` no `.gitignore`).

## 2. Contas conferidas (python3, independentes do planejador)

- Dias da semana: 05/10 seg · **06/10 ter** (relógio) · 07/10 qua · 08/10 qui · 09/10 sex · 10/10 sab · 11/10 dom · **12/10 seg (feriado)** · 13/10 ter · 01/09 ter · 04/09 sex · 05/09 sab · 02/11 seg (feriado do verificador) · 03/11 ter · 14/11 sab · 15/11 dom.
- Grade ter 06/10, sessão 30 min a partir de 11:00 (09:00 + 2 h): 11:00, 11:30 + 14:00…17:30 = 10 × 2 profissionais = **20**; RPG 60 min só Carla: 11:00 + 14:00…17:00 = **8**; avaliação dia inteiro: 7 + 7 = **14**; sábado 08:00…11:30 = 8 × 2 = **16**.
- Chat com 60 min: 11:00 Carla, 11:00 Diego, 14:00 Carla (11:30 não cabe até 12:00); com 06/10 lotado → 07/10 08:00 Carla, 08:00 Diego, 08:30 Carla.
- Confirmação: 09/10 09:00 − 07/10 10:00 = **47 h ≤ 48**.
- Retorno: 07/10 + 30 = **06/11**; aviso a partir de 06/11 − 7 = **30/10** (29/10 não). Verificador: 03/11 + 15 = 18/11; aviso ≥ 15/11.
- Adesão §23: semana 05/10–11/10; prescrição ter 06/10 com `seg,qua,sex` + `ter,qui`; previstos até sex 09/10 = 06, 07, 08, 09 = **4**; feitos 06 e 08 = **2** → **50,0 %**; dor (3 + 5)/2 = **4,0**; `ultima_dor` 5. Verificador: semana 02/11, previstos só 03/11 → 1/1 = 100 %, dor 5.
- Raio-X out/2026: dias úteis seg–sex = 22 − feriado 12/10 = 21 × 480 + 5 sábados × 240 = 11 280 × 2 profissionais = **22 560 min**; ativos 60+30+30+60+30+60 = **270** → ocupação **1,197 %**; `atendimentos_mes` 4 (p1×2, p3, p6); `falta_pct` 1/(4+1) = **20,0**; novos 2 (p6 já tinha realizado em 04/09); retornos de 04/10 e 05/10: p6 cumpriu com avaliação em 07/10 ∈ [04/09, 03/11] → **50,0**; recorrente 4/3 = **1,333**; `orcamentos_mes` 2; `aprovacao_atual_pct` 50. Set/2026: 2, 2, 0, 1,0, 2, 100. Verificador nov/2026: 3 realizados, 1 falta → 25 %; recorrente 3,0; retorno 100 %.
- Verificador, grade de 20 min para 40 min em 07–11: 07:00 … 10:20 = **11** horários.

## 3. Contradições internas — OK

Cada teste sobe o próprio `dados` (`tmp_path`); nenhum depende de estado de outro. Fixture permite todos os cenários (horários dentro dos turnos, Diego sem RPG para o 422, sábado curto, feriado numa segunda, 12 exercícios com os ids obrigatórios e ≥ 6 regiões). `exemplos/clinica.json` = fixture com `nome` e `token` trocados.

## 4. Burlável? — OK após reforço

`verificar-independente.py`: clínica nunca vista (passo 20, antecedência 1 h, abandono 1, reavaliação 1, 15 dias, dor 5, lembrete 07:30, feriado 02/11, 1 profissional, serviços `aval`/`fisio`, exercícios com outros textos, relógio 03/11 06:00), tudo explícito (sem os atalhos `paciente()`/`agenda()`/`plano()`/`prescricao()` do conftest); grep de 10 valores do fixture em `atende src web tools`; 3 SVGs em dois instantes no Chromium; ≥ 6 `<style>` distintos; MP4 e Docker reais. Hash do contrato cobre `tests/ pytest.ini docs/ESPECIFICACAO.md verificar-limites.sh verificar-independente.py` (lido do working tree, então edição não commitada também acusa).

## 5. Raio-X — OK

Os 8 ids existem em `~/projetos/raio-x-margem/setores/clinica.js` (`atendimentos_mes`, `falta_pct`, `ocupacao_pct`, `clientes_novos_mes`, `retorno_atual_pct`, `atendimentos_mes_recorrente` herdados de `servicos.js`; `orcamentos_mes` e `aprovacao_atual_pct` próprios do pacote, grupo `convenio`). Formato do acompanhamento bate com `app/painel-motor.js` linha 6: `{tipo: 'acompanhamento', pacote, cliente, base: {data, valores}, meses: [{mes, valores, obs}]}`.

## 6. Travas — OK (saída real, clone temporário apagado)

`loop.env`: `CODEX_ARGS="-c sandbox_workspace_write.network_access=true"`, `PERMITIDOS="."`, `PROTEGIDOS` = `tests/ pytest.ini docs/` + `goal.md hash-congelado.txt congelar.sh verificar-limites.sh verificar-independente.py loop.env prompt.md`; `TESTE_FINAL` inclui `verificar-limites.sh`. Prompts proíbem API real, rede, `npx`/`npm`/`docker`, `pkill -f` e arquivos protegidos. `.gitignore` cobre `__pycache__/`; `pytest.ini` desliga o cache (`-p no:cacheprovider`) — nada "fora do escopo" nasce do próprio `pytest --collect-only`.

```
== 6a congelar.sh
congelado: HASH=381b6510e90832d5 TESTES=98
== 6b stub honesto (src/x.py com EVOLUTION_API_KEY, "apikey", "@s.whatsapp.net", "http://127.0.0.1:8080"; atende; Dockerfile, docker-compose.yml, .env.exemplo vazios; um SVG só CSS)
LIMITES OK (hash 381b6510e90832d5, 98 testes, escopo ok, sem API/rede)      exit=0
== 6c https://api.telegram.org no codigo
LIMITE VIOLADO: chave/credencial ou API externa no código ou na entrega      exit=1
== 6d SMIL num SVG
LIMITE VIOLADO: SVG com script ou SMIL (seção 21: só animação CSS)           exit=1
== 6e teste alterado
LIMITE VIOLADO: hash do contrato mudou (065af9213a3496d9 ≠ 381b6510e90832d5) exit=1
== 6f arquivo fora do escopo
LIMITE VIOLADO: arquivos fora do escopo: docs/novo.md                        exit=1
== 6g de novo limpo
LIMITES OK (hash 381b6510e90832d5, 98 testes, escopo ok, sem API/rede)      exit=0
```

## 7. Harness — OK (saída real)

```
python3 -m pytest -q --collect-only | tail -1   → 98 tests collected
python3 -m pytest -q                             → 23 failed, 75 errors (0 passed; sem ./atende)
stub ./atende (PORTA=<n> + /api/saude com VERSION) → tests/test_basico.py: 5 failed, 1 passed (só test_saude_traz_versao_do_arquivo)
Externo falso: falhas=1 → HTTP 500, 201, 200; pedidos registrados com rota/status/apikey/number; whats()=1, whats(ok=False)=2, telegram()=1
```

## 8. Tamanho e fechamento — OK

"Fora do v1" (§12) é claro. Nenhum teste exige rede real, Docker real (teste de Docker é estático; o build real fica no nível 4) ou relógio real (tudo por `ATENDE_AGORA`/`agora` da rodada). MP4/HyperFrames fora do pytest e do loop. 20 ciclos × 30 min para 98 testes (o irmão fechou 93 em 7 ciclos).

## 9. README "Como rodar no seu ambiente" — OK

Caminhos citados existem (`~/projetos/execucao-longa/tools/loop-longrun.sh`, `prompt-goal-claude.md`, `prompt-goal-codex.md`, `congelar.sh`, `verificar-independente.py`). Os três caminhos de execução estão descritos; pré-requisitos batem com os do `loop-longrun.sh`. Comando de render da §25 (`npx hyperframes render <dir> --output <x>.mp4 --quality looks --fps 30`) conferido em `~/.claude/skills/hyperframes-cli/references/preview-render.md`; o adaptador `css` existe (`~/.claude/skills/hyperframes-animation/adapters/css-animations.md`) e exige `data-duration` no root para `infinite` — a §25 já põe `data-duration="4"`. Node 24 e FFmpeg presentes nesta máquina; HyperFrames não instalado (render sai `PULADO`).

## 10. Vazamento de processo — OK (saída real)

`conftest.py` já tem `SERVIDORES` + fixture `autouse` que para todos no teardown. Prova: teste temporário que sobe `Servidor` e faz `assert False` antes do `parar()` → `1 failed`; depois do pytest, `pgrep -af 'atende serve'` → `[]`. Teste e stub apagados.

## Prova de movimento (função real do verificador, SVG de teste com `@keyframes` de 2 s)

```
binario_chromium(): /snap/bin/chromium
snap: 2703 2701 diferem
playwright chrome: 2569 2701 diferem
headless-shell (excluido): 2706 2706 IGUAIS
```
Antes da correção, o mesmo snap com screenshot em `/tmp` não gravava arquivo (confinamento) e o verificador acusaria "SVG não se mexe".

## Para o dono decidir (não corrigido de propósito)

- **Decisão 20 ⚠** — `caiu`/`queda`/`inchou` como palavra inteira abrem fila alta em frases como "a dor caiu bastante". Falso positivo é barato; o fisioterapeuta confirma a lista.
- **Decisão 21** — alerta de abandono reemitido por comparação de data (`alerta_abandono` < `inicio` do último realizado); presença marcada atrasada para horário anterior ao alerta não reinicia a sequência.
- Playwright (Python) não está instalado nesta máquina; a prova de movimento usa o Chromium do snap (funciona). HyperFrames não instalado: instalar (`npx hyperframes --version` baixa o pacote) para a etapa 4 sair de `PULADO`.
