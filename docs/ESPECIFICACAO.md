# Especificação v1 — atende-fisioterapia (contrato congelado)

> Este arquivo é **protegido** durante a execução longa: o agente implementa contra ele e não o altera.
> Os testes em `tests/` verificam exatamente o que está aqui. Mudança de contrato = humano edita, recongela o hash e reinicia o longrun.

## O que muda em relação ao atende-clinica

Este sistema é o `atende-clinica` adaptado a **uma clínica de fisioterapia**. Tudo o que não está listado aqui é igual ao molde (`~/projetos/atende-clinica/docs/ESPECIFICACAO.md`):

| Tema | atende-clinica | atende-fisioterapia |
|---|---|---|
| Serviços do exemplo | odonto (avaliação, limpeza, canal) | `avaliacao` 60 min, `sessao` 30 min, `rpg` 60 min (seção 2) |
| Conselho do exemplo | `cfo` | `coffito` (COFFITO 424/2013); a tabela de travas continua com os 4 perfis (seção 9) e ganha o código `depoimento` |
| Retorno programado | `retorno_dias` por serviço | **não existe `retorno_dias`**; o retorno (reavaliação) nasce quando um **plano de tratamento é concluído** (seções 8 e 20) |
| Página da equipe | `/recepcao` | `/equipe` (seção 13), com planos, prescrições, adesão, biblioteca e alertas |
| Conversa | 8 regras | 12 regras: alerta clínico, lembrete, adesão/dor e explicação de exercício (seção 6) |
| `tarefas/rodar` | confirmação, retorno, reenvio | + lembrete de exercícios + alertas de abandono/reavaliação (seções 22 e 24) |
| Raio-X | 5 valores | + `atendimentos_mes_recorrente`, `orcamentos_mes`, `aprovacao_atual_pct` (seção 10) |
| LGPD | paciente, agendamentos, mensagens | + planos, prescrição, registros de adesão/dor (seção 11) |
| Evolution | `sendText` | + `sendMedia` com o MP4 do exercício quando existir (seção 17) |
| Telegram | `/responder /encerrar /fila /agenda` | + `/alertas` (seção 18) |
| Variáveis novas | — | `PUBLIC_URL`, `EXERCICIOS_MP4_DIR` (seções 17, 19, 21) |
| Novo | — | planos (20), biblioteca de exercícios com SVG animado (21), prescrição e lembretes (22), adesão/dor/alertas clínicos (23), alertas à equipe (24), MP4 pelo HyperFrames (25) |

## 0. O que é

Sistema de atendimento ao paciente para **uma clínica de fisioterapia**: agenda de avaliação e sessões, confirmação automática, lista de espera, plano de tratamento com alerta de abandono e de reavaliação, exercícios domiciliares prescritos com lembrete, registro de adesão e dor, explicação animada de cada exercício, tirar dúvidas (FAQ), passagem para humano, emergência, campanhas com trava de conselho/LGPD e exportação de números para o **Painel de Recuperação do Raio-X de Margem**.

Canais: **chat web**, **WhatsApp pela Evolution API** (seção 17) e caixa de saída **simulada** quando a Evolution não está configurada. Equipe interna atende pelo **Telegram** (seção 18) e pela página da equipe. Cadastros (seção 14), gestão de agenda (seção 15), backup do banco (seção 16) e entrega em **Docker** para VPS (seção 19).

O bot **nunca** dá orientação clínica, diagnóstico, remédio ou exercício fora do que o fisioterapeuta prescreveu: explica o que está no catálogo **e** na prescrição do paciente; o resto vai para o humano.

## 1. Execução

- Ponto de entrada: arquivo executável `./atende` na raiz do repo.
- `./atende serve --porta N --dados DIR [--host H]`
  - `--porta 0` = porta livre escolhida pelo sistema. A **primeira linha** do stdout é `PORTA=<n>` (com flush), impressa quando o servidor já aceita conexões.
  - Escuta em `--host` (padrão `127.0.0.1`; no Docker, `0.0.0.0` passado pelo comando do container — nunca escrito no código).
  - `DIR/clinica.json` = configuração (seção 2). Se não existir, copiar `exemplos/clinica.json`. `DIR` é criado se não existir.
  - Todo o estado persiste em `DIR/` (ex.: SQLite). Reiniciar com o mesmo `DIR` mantém tudo.
  - O servidor aceita conexões simultâneas (10 pedidos ao mesmo tempo não podem ser recusados por fila cheia).
- **Relógio:** variável de ambiente `ATENDE_AGORA` (`AAAA-MM-DDTHH:MM`, hora local da clínica, sem fuso) fixa o "agora" do processo. Sem ela, usa o relógio real. Datas/horas no contrato são sempre `AAAA-MM-DDTHH:MM` local; datas, `AAAA-MM-DD`; horas, `HH:MM`.
- `./atende raiox --dados DIR --mes AAAA-MM --acompanhamento ARQ` (seção 10).
- `./atende backup` / `./atende restaurar` (seção 16).
- `tools/render-exercicios` (seção 25) é passo de build do humano, fora do servidor.
- Integrações externas **só** por variáveis de ambiente (seções 17–19). Sem elas, nenhuma chamada de rede sai do processo. Nenhuma URL externa, chave ou token escrito no código.

## 2. `clinica.json`

```json
{
  "nome": "Fisio Movimento",
  "conselho": "coffito",             // cfm | cfo | coffito | estetica
  "token": "segredo",               // exigido no header X-Token das rotas da equipe
  "passo_min": 30,                   // grade de horários
  "antecedencia_min_horas": 2,       // não oferece/aceita horário antes de agora + isto
  "janela_dias": 14,                 // até quantos dias à frente o chat oferece horários
  "confirmacao_horas": 48,           // pede confirmação quando a sessão começa em até 48 h
  "retorno_aviso_dias": 7,           // avisa a reavaliação quando faltam até 7 dias
  "abandono_faltas": 2,              // faltas seguidas num plano ativo → alerta de abandono
  "reavaliacao_sessoes": 2,          // restantes ≤ isto → alerta de reavaliação
  "reavaliacao_dias": 30,            // plano concluído → retorno em última sessão + 30 dias
  "dor_alerta": 7,                   // dor ≥ 7 → fila humana alta
  "lembrete_hora_padrao": "19:00",   // hora do lembrete quando o paciente não escolhe
  "feriados": ["2026-10-12"],
  "horarios": { "seg": [["08:00","12:00"],["14:00","18:00"]], "ter": [...], "qua": [...], "qui": [...], "sex": [...], "sab": [["08:00","12:00"]], "dom": [] },
  "profissionais": [ { "id": "carla", "nome": "Carla Souza", "servicos": ["avaliacao","sessao","rpg"] } ],
  "servicos": [ { "id": "sessao", "nome": "Sessão de fisioterapia", "duracao_min": 30 } ],
  "faq": [ { "id": "convenios", "perguntas": ["vocês aceitam convênio"], "resposta": "Atendemos Unimed e particular." } ],
  "exercicios": [ { "id": "ponte", "nome": "Ponte", "apelidos": ["ponte de glúteo"], "regiao": "lombar e quadril",
                    "passos": ["..."], "erros_comuns": ["..."], "cuidados": ["..."], "contraindicacoes": ["..."], "pare_se": ["..."] } ]
}
```

Dias da semana: `seg ter qua qui sex sab dom`. Serviço **não** tem `retorno_dias`. Os campos novos (`abandono_faltas`, `reavaliacao_sessoes`, `reavaliacao_dias`, `dor_alerta`, `lembrete_hora_padrao`) são obrigatórios no exemplo; se faltarem no arquivo, valem os valores acima.

## 3. Regras de agenda

- Horário candidato: começa no início de uma janela e anda de `passo_min` em `passo_min`; vale se `[inicio, inicio+duracao)` cabe inteiro na janela.
- **Inválido (422)** se: não é horário candidato (fora da grade ou não cabe na janela); dia em `feriados`; `inicio < agora + antecedencia_min_horas`; profissional não faz o serviço ou está inativo; horário dentro de bloqueio (seção 15); `plano_id` informado que não é um plano `ativo` do mesmo paciente e do mesmo serviço.
- **Ocupado (409)** se é válido mas sobrepõe outro agendamento **ativo** do mesmo profissional (ou, sem profissional indicado, de todos que fazem o serviço).
- `GET /api/horarios` lista só horários válidos e livres.
- Agendamento ativo = status `agendado`, `confirmado`, `realizado` ou `falta`. `cancelado` libera o horário.
- Dois pedidos simultâneos para o mesmo horário/profissional: exatamente um vence (201), o outro recebe 409.

## 4. Autenticação

Rotas marcadas **[R]** (equipe) exigem header `X-Token` igual a `clinica.json.token`; sem ele ou errado → **401**, verificado **antes** de ler o corpo (um `POST {}` sem token é 401, não 422). Rotas públicas: `/`, `/equipe` (página; os dados vêm de rotas [R]), `/exercicios/...`, `/api/saude`, `GET /api/servicos`, `GET /api/exercicios`, `/api/horarios`, `/api/mensagens`. Webhooks têm segredo próprio (seções 17 e 18).

## 5. API HTTP (JSON, UTF-8)

Toda resposta JSON vai com `Content-Type: application/json`. Id inexistente no caminho ou no corpo → 404; valor inválido → 422; conflito de estado → 409.

| Método e rota | Corpo | Resposta |
|---|---|---|
| `GET /api/saude` | — | 200 `{"ok": true, "versao": "<conteúdo de VERSION>"}` |
| `GET /api/servicos` | — | 200 `{"servicos": [{id, nome, duracao_min}]}` só ativos, na ordem de cadastro |
| `GET /api/horarios?servico=S&data=AAAA-MM-DD[&profissional=P]` | — | 200 `{"horarios": [{"inicio", "profissional"}]}` ordenado por `inicio`, depois `profissional` (texto); serviço inexistente → 404 |
| `POST /api/pacientes` [R] | `{nome, telefone, consentimento_marketing?: bool}` | 201 `{id}`; telefone já cadastrado → 200 com o mesmo `{id}`; telefone inválido → 400 |
| `POST /api/agendamentos` [R] | `{paciente_id, servico, inicio, profissional?, plano_id?}` | 201 `{id, status: "agendado", inicio, fim, profissional, plano_id}`; sem `profissional` = o primeiro livre por ordem de `id`; sem `plano_id` = o plano `ativo` do paciente com o mesmo `servico`, se houver (senão `null`); horário ocupado → 409; inválido (regra 3) → 422; paciente/serviço inexistente → 404 |
| `GET /api/agendamentos?data=AAAA-MM-DD` [R] | — | 200 `{"agendamentos": [{id, paciente_id, telefone, servico, profissional, inicio, fim, status, plano_id}]}` todos os status, ordem de `inicio` e depois `id` |
| `POST /api/agendamentos/{id}/cancelar` [R] | — | 200 `{status: "cancelado"}`; dispara a lista de espera (seção 7) |
| `POST /api/agendamentos/{id}/remarcar` [R] | `{inicio}` | 200 com o agendamento no novo horário (mesmo `id`, status `agendado`); mesmas regras de 409/422 |
| `POST /api/agendamentos/{id}/presenca` [R] | `{compareceu: bool}` | 200 `{status: "realizado" \| "falta"}`; atualiza o plano vinculado (seção 20); pode ser marcada a qualquer momento (não depende do relógio); segunda chamada no mesmo agendamento → 409 |
| `POST /api/espera` [R] | `{paciente_id, servico, data}` | 201 `{id}` |
| `POST /api/tarefas/rodar` [R] | `{agora?}` (padrão = relógio do processo; vale só para esta rodada) | 200 `{"enviadas": n, "alertas": n}` (+ `"reenviadas"` com a Evolution); idempotente: rodar de novo no mesmo instante → tudo 0 |
| `GET /api/saida` [R] | — | 200 `{"mensagens": [{id, tipo, telefone, paciente_id, texto, agendamento_id, status}]}` em ordem de criação. `tipo` ∈ `confirmacao, espera, retorno, campanha, humano, prescricao, exercicio, explicacao` (`exercicio` = lembrete diário da seção 22; `explicacao` = resposta da regra 9 da seção 6). Ids de todo recurso são inteiros, crescentes na ordem de criação |
| `POST /api/mensagens` | `{telefone, texto}` | 200 `{"respostas": [texto, ...]}` (seção 6) |
| `GET /api/atendimento-humano` [R] | — | 200 `{"fila": [{id, telefone, nome, motivo, prioridade, status}]}` só os `aberto`, ordem de `id`; `prioridade` ∈ `normal, alta` |
| `POST /api/campanhas` [R] | `{texto}` | 200 `{"enviadas": n}` ou 422 `{"violacoes": [codigos]}` (seção 9) |
| `GET /api/pacientes/{id}/dados` [R] | — | 200 `{paciente, agendamentos, mensagens, planos, prescricao, registros}` (LGPD art. 18, II) |
| `DELETE /api/pacientes/{id}` [R] | — | 204; anonimiza (seção 11); `GET .../dados` continua respondendo 200 |
| `GET /api/raiox?mes=AAAA-MM` [R] | — | 200 (seção 10) |

Telefone: aceita com ou sem `+55`, espaços, parênteses e hífen; normaliza para `+55DDNNNNNNNNN` (DDD + 8 ou 9 dígitos; 10 ou 11 dígitos sem o 55, 12 ou 13 com ele). Fora disso → inválido. Todas as respostas usam o telefone normalizado.

**Envio síncrono:** `tarefas/rodar`, `campanhas`, `POST .../prescricao`, `.../responder` e `/responder` do Telegram só devolvem a resposta HTTP depois de tentar os envios (o `status` da mensagem já está definido ao responder). Respostas ao webhook da Evolution e avisos ao Telegram podem ser assíncronos.

## 6. Conversa (`POST /api/mensagens`)

O texto é normalizado (minúsculas, sem acento, pontuação trocada por espaço) antes de decidir. "Contém X" = X aparece como **sequência de palavras inteiras** no texto normalizado (`fiz` não casa `fizemos`; `dor 7` exige as duas palavras seguidas, então `minha dor hoje e 7` não casa), **exceto** na regra 1, que usa substring como no atende-clinica. Ordem de decisão (a primeira que casa decide):

1. **Emergência** — o texto contém (substring) um destes: `dor no peito`, `falta de ar`, `desmaio`, `desmaiou`, `sangramento`, `sangrando`, `convulsao`, `suicidio`, `me matar`, `avc`, `infarto`. Resposta contém `192` e `pronto-socorro`; entra na fila humana com `prioridade: "alta"` e `motivo: "emergencia"`. Não agenda nem registra nada.
2. **Alerta clínico** — palavras inteiras: `dormencia`, `dormente`, `formigamento`, `perda de forca`, `sem forca`, `perdi a forca`, `febre`, `irradia`, `irradiando`, `queda`, `caiu`, `tombo`, `inchaco`, `inchou`, `inchado`, `nao consigo andar`, `nao consigo mexer`, `perdi o controle`. Resposta contém `fisioterapeuta` e `192` e **não** contém orientação (nada de "faça", "tome", "alongue"); fila humana `prioridade: "alta"`, `motivo: "alerta clinico"`. Nada mais é registrado.
3. **Parar** — texto igual a `parar`, `sair` ou `pare`: paciente fica `nao_contatar`; resposta contém `não vai mais receber`. Nenhuma mensagem de saída (confirmação, retorno, campanha, espera, prescrição, lembrete de exercício) vai mais para esse telefone.
4. **Humano** — contém `atendente`, `humano` ou `falar com alguem`: fila humana `prioridade: "normal"`; resposta contém `atendente`.
5. **Fluxo em andamento** (agendamento pelo chat, abaixo) consome a mensagem.
6. **Resposta a pendência** — vale a **última mensagem da caixa de saída** (`/api/saida`) para o telefone, **se ela for de um dos três tipos abaixo** e ainda estiver sem resposta (`prescricao`, `explicacao`, `humano`, `campanha` e `retorno` não são pendência: uma delas por último = sem pendência). O texto normalizado é comparado por **igualdade**:
   - `confirmacao`: igual a `1`, `sim` ou `confirmo` → status `confirmado`, resposta contém `confirmad`; igual a `2`, `cancelar` ou `nao` → `cancelado` (dispara espera), resposta contém `cancelad`. Outro texto → segue para as regras seguintes (a pendência continua).
   - `espera`: igual a `1` ou `sim` → agenda o horário ofertado se ainda livre (resposta contém `agendad`), senão resposta contém `ocupado`.
   - `exercicio` (lembrete, seção 22): texto que é só um número de `0` a `10` → registra **dor** desse valor (seção 23); `fiz` / `nao fiz` / `dor N` seguem a regra 8.
7. **Lembrete** — paciente com prescrição ativa: `lembrete HH:MM` ou `lembrete` sozinho (= `lembrete_hora_padrao`) liga o lembrete nessa hora; `sem lembrete` desliga. A hora é lida do **texto original** (antes de normalizar) por `\d{1,2}:\d{2}`; hora inválida (ex.: `25:99`) → resposta contém `lembrete` e nada muda. Resposta contém `lembrete` e, ao ligar, `HH:MM`. Sem prescrição ativa → cai na regra 12.
8. **Adesão e dor** — paciente cadastrado (telefone conhecido): `fiz` → `fez: true`; `nao fiz` ou `nao consegui` → `fez: false` (exigem prescrição ativa; sem ela → regra 12); `dor N` (N inteiro 0–10) → `dor: N` (não exige prescrição). Um texto pode trazer os dois (`fiz, dor 3`). Tudo no **dia do relógio do processo** (seção 23). Resposta contém `registrad`. Se `N ≥ dor_alerta`: fila humana `prioridade: "alta"`, `motivo: "dor N"`, e a resposta contém também `fisioterapeuta` e `192`. Telefone desconhecido → regra 12.
9. **Exercício** — o texto contém o `nome` ou um `apelido` (normalizados) de um exercício **ativo** do catálogo; mais de um casa → o de maior número de palavras no termo casado, empate → o primeiro na ordem do catálogo. Se o exercício está na **prescrição ativa** do paciente: resposta com o nome, os `passos` numerados (`1. ...`), a linha `Pare se: <pare_se separados por "; ">` e o link `<PUBLIC_URL>/exercicios/<id>` (sem `PUBLIC_URL`, só `/exercicios/<id>`); essa resposta **também entra na caixa de saída** como `tipo: "explicacao"` (`status: "simulado"` sem Evolution; com Evolution, seção 17). Se não está prescrito (ou o telefone não tem cadastro/prescrição): resposta contém `fale com seu fisioterapeuta` e `atendente`, **sem** passos. Texto com a palavra `exercicio`/`exercicios` sem casar nome: lista os exercícios prescritos (`- <nome> — <link>`), ou a mesma resposta de "não prescrito".
10. **Agendar** — contém `agendar`, `marcar` ou `consulta`: inicia o fluxo.
11. **FAQ** — palavras significativas (≥ 3 letras, fora de artigos/preposições/pronomes comuns) de alguma pergunta do FAQ: se ≥ 60 % delas aparecem no texto, responde **exatamente** a `resposta` daquele item (só ela, uma mensagem). Mais de um item casa → o de maior %; empate → o primeiro do FAQ.
12. **Não entendi** — resposta contém `não entendi` e oferece `atendente`. Na **segunda** seguida sem entender, entra na fila humana (`normal`) automaticamente.

**Fluxo de agendamento pelo chat** (estado por telefone, persistido):
- telefone sem paciente → pergunta o nome (resposta contém `nome`); a próxima mensagem vira o nome e o paciente é criado (`consentimento_marketing: false`). Paciente conhecido não ouve pergunta de nome.
- lista os serviços ativos numerados `1 - <nome>` na ordem de cadastro;
- escolhido o número, oferece os **3 primeiros** horários livres a partir de `agora + antecedencia_min_horas`, dentro de `janela_dias`, em todos os profissionais, ordem da seção 5; cada linha `N) DD/MM HH:MM com <nome do profissional>`;
- escolhido o número, cria o agendamento (vinculado ao plano ativo do serviço, se houver); resposta contém `agendad`, `DD/MM` e `HH:MM`.
- número inválido em qualquer passo → repete as opções. `cancelar` dentro do fluxo → sai do fluxo.
- O bot **nunca** inventa preço, diagnóstico, remédio ou exercício: fora do FAQ e da prescrição cai na regra 12.

Enquanto um atendimento humano do telefone estiver `aberto` (seção 18), o bot não responde (`respostas: []`), exceto as regras 1 e 2.

## 7. Lista de espera

Ao cancelar (pela API ou pela conversa), o primeiro pedido de espera ainda não atendido com o mesmo `servico` e a mesma `data` do horário liberado (ordem de criação), cujo paciente não esteja `nao_contatar`, recebe mensagem `tipo: "espera"` contendo `HH:MM` do horário e `1`. O pedido fica `ofertado` (não recebe outra oferta do mesmo horário).

## 8. Confirmação e retorno (`POST /api/tarefas/rodar`)

- **Confirmação:** todo agendamento `agendado` com `agora < inicio ≤ agora + confirmacao_horas` que ainda não recebeu confirmação → mensagem `tipo: "confirmacao"` com `agendamento_id`. Texto contém o nome do serviço, `DD/MM`, `HH:MM`, `1` (confirmar) e `2` (cancelar). **Não contém valor em R$.**
- **Retorno (reavaliação):** quando um plano fica `concluido` (seção 20) nasce um retorno com `servico: "avaliacao"` (o serviço de avaliação do plano, campo `servico_avaliacao` do plano; padrão `avaliacao`) e `data = data da última sessão realizada + reavaliacao_dias`. Quando `agora ≥ data − retorno_aviso_dias` e ainda não avisado → mensagem `tipo: "retorno"` com a palavra `reavalia` e o nome do serviço. Uma vez só.
- Paciente `nao_contatar` nunca recebe (a mensagem **não é criada**). Lembrete, retorno e prescrição **não** dependem de `consentimento_marketing` (LGPD art. 11, II, f — tutela da saúde).
- `enviadas` conta as mensagens **criadas** nesta rodada (confirmação, retorno, lembrete de exercício), mesmo que o envio pela Evolution falhe (`pendente`).

## 9. Campanhas e trava de conselho

`POST /api/campanhas {texto}` envia só para pacientes com `consentimento_marketing: true` e sem `nao_contatar` (LGPD art. 11, I — consentimento específico). Antes de enviar, valida o texto em minúsculas e sem acento (**pontuação mantida**, para `r$` e `100%`). O `422` lista **todos** os códigos violados. Qualquer violação → 422 e nada é enviado.

| Código | Detecta | cfm | cfo | coffito | estetica |
|---|---|---|---|---|---|
| `promessa_resultado` | `garantido`, `garantia de resultado`, `100%`, `resultado garantido` | ✔ | ✔ | ✔ | ✔ |
| `melhor_profissional` | `melhor medico`, `melhor dentista`, `melhor fisioterapeuta`, `melhor clinica` | ✔ | ✔ | ✔ | — |
| `sorteio_brinde` | `sorteio`, `brinde`, `premio`, `premiacao` | ✔ | ✔ | — | — |
| `antes_depois` | `antes e depois` | ✔ | ✔ | — | — |
| `consorcio` | `consorcio` | ✔ | — | — | — |
| `preco` | `r$`, `reais` | — | ✔ | ✔ | — |
| `parcelamento` | `parcela`, `parcelamento`, `sem juros`, `10x` (qualquer `<n>x`) | — | ✔ | — | — |
| `gratuito` | `gratis`, `gratuito`, `gratuita` | — | ✔ | ✔ | — |
| `promocao` | `promocao`, `desconto`, `oferta` | — | — | ✔ | — |
| `depoimento` | `depoimento`, `carta de agradecimento`, `agradecimento de paciente` | — | — | ✔ | — |

Bases: CFM 2.336/2023 arts. 9º e 11; CFO 118/2012 art. 44 + 196/2019 + 271/2025; COFFITO 424/2013 arts. 10 (V), 39 e 40. Fonte e leitura em `raio-x-margem/docs/setores/servicos-pesquisa-2026-10.md`.

## 10. Exportação para o Raio-X (Painel de Recuperação)

`GET /api/raiox?mes=AAAA-MM` → `{"pacote": "clinica", "mes": "AAAA-MM", "valores": {...}}`, números com 1 casa decimal (os testes toleram ±0,06):

- `atendimentos_mes` = agendamentos `realizado` com `inicio` no mês (inteiro);
- `falta_pct` = `falta ÷ (realizado + falta) × 100` (0 se não houver);
- `ocupacao_pct` = minutos de agendamentos ativos no mês ÷ minutos disponíveis no mês (todas as janelas de todos os profissionais ativos, menos feriados) × 100;
- `clientes_novos_mes` = pacientes cujo **primeiro** `realizado` cai no mês;
- `retorno_atual_pct` = dos retornos com `data` no mês, % cujo paciente tem agendamento `realizado` do mesmo serviço entre `data − 30 dias` e `data + 30 dias` (0 se não houver retornos);
- `atendimentos_mes_recorrente` = `atendimentos_mes ÷ pacientes distintos com realizado no mês` (0 se não houver);
- `orcamentos_mes` = planos de tratamento **criados** no mês (inteiro; qualquer status);
- `aprovacao_atual_pct` = desses planos, % com pelo menos uma sessão `realizado` vinculada (0 se não houver planos).

`./atende raiox --dados DIR --mes M --acompanhamento ARQ`: lê `ARQ` (formato do `raio-x-margem/app/painel-motor.js`: `{tipo: "acompanhamento", pacote, cliente, base: {data, valores}, meses: [{mes, valores, obs}]}`), insere ou substitui o mês `M` com `valores` = os da rota acima **mesclados** sobre os valores do mês anterior (ou da base) e `obs: "atende-fisioterapia"`, e grava de volta. Campos que o sistema não mede (ex.: `ticket_medio`, `glosa_pct`) ficam como estavam. Sai com código 0.

## 11. LGPD

- `GET /api/pacientes/{id}/dados` devolve tudo o que há do paciente: `paciente` `{id, nome, telefone, consentimento_marketing, nao_contatar, lembrete_hora, lembrete_ativo}`, `agendamentos` (formato da listagem), `mensagens` = recebidas e enviadas, cada uma `{direcao: "entrada" | "saida", texto, quando}`, `planos` (formato da seção 20), `prescricao` (a ativa, formato da seção 22, ou `null`) e `registros` (seção 23).
- `DELETE /api/pacientes/{id}`: nome vira `removido`, telefone vira `null`, agendamentos `agendado`/`confirmado` viram `cancelado` (os `realizado`/`falta` ficam), textos de mensagens dele viram `""`, planos `ativo` viram `encerrado`, a prescrição fica inativa (`prescricao: null`, lembrete desligado) e os `registros` são apagados (`[]`). Depois disso, mensagens ao telefone antigo são tratadas como de telefone desconhecido. Números agregados do `/api/raiox` continuam contando os atendimentos e planos passados.

## 12. Fora do v1 (não implementar; portão humano ou próxima versão)

WhatsApp Cloud API oficial da Meta (v1 usa a Evolution), SMS/e-mail, deploy na VPS (é do humano: README explica), cobrança/pacote pago por Pix e planos/assinatura (PSP), prontuário e evolução clínica, convênio/glosa/TISS, várias clínicas no mesmo servidor, login por usuário, LLM nas respostas (pode entrar depois atrás de uma opção desligada por padrão; os testes nunca a usam), interface EN/ES, vídeo com pessoa real, geração automática dos SVGs por IA, envio de foto/vídeo pelo paciente.

## 13. Páginas

- `GET /` → HTML do chat do paciente, com elemento `id="chat"`, que usa `/api/mensagens`.
- `GET /equipe` → HTML da equipe com elementos `id="agenda"`, `id="fila-humano"`, `id="saida"`, `id="pacientes"`, `id="planos"`, `id="prescricoes"`, `id="adesao"`, `id="biblioteca"` e `id="alertas"`; pede o token e usa as rotas [R] (cadastros, agenda, planos, prescrição por paciente, adesão e dor por paciente, biblioteca de exercícios, alertas, fila humana com responder/encerrar).
- `GET /exercicios/{id}` e `GET /exercicios/{id}.svg` → seção 21.

## 14. Cadastros [R]

`clinica.json` é lido a cada início para `nome, conselho, token, passo_min, antecedencia_min_horas, janela_dias, confirmacao_horas, retorno_aviso_dias, abandono_faltas, reavaliacao_sessoes, reavaliacao_dias, dor_alerta, lembrete_hora_padrao, feriados, horarios`. Já `profissionais`, `servicos`, `faq` e `exercicios` só **semeiam** o banco na primeira vez (banco vazio); depois o banco é a fonte e se edita pela API.

| Método e rota | Corpo | Resposta |
|---|---|---|
| `GET /api/profissionais` | — | 200 `{"profissionais": [{id, nome, servicos, registro, horarios, ativo}]}` (`registro` = CREFITO, pode ser `null`; `horarios` = `null` quando usa o da clínica), ordem de cadastro |
| `POST /api/profissionais` | `{id, nome, servicos, registro?, horarios?}` | 201; `id` repetido → 409; serviço inexistente → 422 |
| `PUT /api/profissionais/{id}` | campos parciais | 200 com o registro atualizado; inexistente → 404 |
| `DELETE /api/profissionais/{id}` | — | 200 `{"ativo": false}`. Inativo some de `/api/horarios`, do chat e não aceita agendamento novo (422); os agendamentos já feitos continuam |
| `GET /api/servicos` (público) | — | só os ativos |
| `POST /api/servicos` | `{id, nome, duracao_min}` | 201; `id` repetido → 409 |
| `PUT /api/servicos/{id}` / `DELETE /api/servicos/{id}` | parcial / — | 200 / 200 `{"ativo": false}` (some da lista pública e do chat) |
| `GET /api/pacientes?busca=T` | — | 200 `{"pacientes": [{id, nome, telefone, email, nascimento, consentimento_marketing, nao_contatar}]}` ordem de `id`; `busca` casa parte do nome (sem acento, sem caixa) ou dígitos do telefone; sem `busca` = todos |
| `POST /api/pacientes` | aceita também `email`, `nascimento` (`AAAA-MM-DD`) | igual à seção 5 |
| `PUT /api/pacientes/{id}` | `{nome?, telefone?, email?, nascimento?, consentimento_marketing?, nao_contatar?}` | 200 com o paciente; telefone inválido → 400; telefone de outro paciente → 409 |
| `GET /api/faq` | — | 200 `{"faq": [{id, perguntas, resposta}]}` ordem de cadastro |
| `POST /api/faq` | `{perguntas: [..], resposta}` | 201 `{id}`; o bot passa a usar na hora |
| `DELETE /api/faq/{id}` | — | 204; o bot para de usar na hora |

Biblioteca de exercícios: seção 21.

## 15. Gestão de agenda [R]

- **Horário por profissional:** `horarios` do profissional (mesmo formato da clínica) substitui o da clínica só para ele. `null` = o da clínica.
- **Bloqueios** (férias, folga, congresso): `POST /api/bloqueios {profissional, inicio, fim, motivo}` → 201 `{id, conflitos: [ids de agendamentos ativos que caem no bloqueio]}` (não cancela nada sozinho). Horários que sobrepõem `[inicio, fim)` somem de `/api/horarios` e o agendamento neles dá 422. `GET /api/bloqueios?profissional=P` → 200 `{"bloqueios": [{id, profissional, inicio, fim, motivo}]}` ordem de `id`. `DELETE /api/bloqueios/{id}` → 204 e libera.
- **Listagem por período:** `GET /api/agendamentos?de=AAAA-MM-DD&ate=AAAA-MM-DD[&profissional=P]` (inclusivo nas duas pontas), ordenado por `inicio` e `id`; continua valendo `?data=`.

## 16. Banco de dados

- `./atende backup --dados DIR --saida ARQ` → grava em `ARQ` uma cópia consistente de todo o estado (pode rodar com o servidor ligado). Código 0.
- `./atende restaurar --dados DIR --entrada ARQ` → com o servidor parado, substitui o estado de `DIR` pelo do backup. Código 0. Ao subir de novo, tudo volta como estava no momento do backup.

## 17. WhatsApp pela Evolution API

Variáveis: `EVOLUTION_URL` (endereço da Evolution; no compose costuma ser o nome do serviço na rede interna), `EVOLUTION_API_KEY`, `EVOLUTION_INSTANCIA`, `WEBHOOK_SEGREDO`, `PUBLIC_URL` (endereço HTTPS público deste sistema, sem barra final; usado só para montar links e `media`). Sem `EVOLUTION_URL` → canal simulado (só caixa de saída, `status: "simulado"`). Nenhum desses valores de exemplo entra no código nem no `.env.exemplo` (lá ficam vazios).

**Entrada** — `POST /webhook/evolution/{WEBHOOK_SEGREDO}` (segredo errado → 404). Formato da Evolution v2:
```json
{"event": "messages.upsert", "instance": "clinica",
 "data": {"key": {"remoteJid": "5541999990001@s.whatsapp.net", "fromMe": false, "id": "ABC123"},
          "pushName": "Maria", "message": {"conversation": "oi"}, "messageType": "conversation"}}
```
- Sempre responde 200. Ignora: `event` diferente de `messages.upsert`, `fromMe: true`, `remoteJid` de grupo (`@g.us`), `key.id` já processado (a Evolution reenvia).
- Texto = `message.conversation` ou `message.extendedTextMessage.text`. Sem texto (áudio, imagem...) → responde `Por enquanto só consigo ler mensagens de texto.`
- Telefone = dígitos do `remoteJid` antes do `@`, normalizado como na seção 5. Passa pela mesma conversa da seção 6 (o mesmo paciente, o mesmo estado).
- Cada resposta da conversa vai por `POST {EVOLUTION_URL}/message/sendText/{EVOLUTION_INSTANCIA}` com header `apikey: {EVOLUTION_API_KEY}` e corpo `{"number": "<dígitos com 55>", "text": "<texto>"}`, na ordem.
- **Exceção — explicação de exercício prescrito (regra 9):** se existir o arquivo `{EXERCICIOS_MP4_DIR}/{id}.mp4` **e** `PUBLIC_URL` estiver definida, a resposta vai por `POST {EVOLUTION_URL}/message/sendMedia/{EVOLUTION_INSTANCIA}` (mesmo header) com `{"number", "mediatype": "video", "media": "{PUBLIC_URL}/exercicios/{id}.mp4", "caption": "<o mesmo texto da regra 9>"}`; senão vai por `sendText` com o texto (que já traz o link da página). Nos dois casos a mensagem entra na caixa de saída com `tipo: "explicacao"` (nunca `exercicio`, que é só o lembrete diário e vale como pendência da regra 6).

**Saída** (confirmação, espera, retorno, campanha, humano, prescrição, lembrete de exercício): com a Evolution configurada, cada mensagem da caixa de saída é enviada do mesmo jeito. Em `/api/saida` cada mensagem tem `status`: `enviado` (2xx), `pendente` (erro HTTP ou de conexão) ou `simulado`. `POST /api/tarefas/rodar` reenvia as `pendente` e devolve também `"reenviadas": n` (as que viraram `enviado`).

## 18. Atendimento interno pelo Telegram

Variáveis: `TELEGRAM_API_URL`, `TELEGRAM_TOKEN`, `TELEGRAM_CHAT_ID` (grupo da equipe), `TELEGRAM_SEGREDO`. Sem elas, nada vai ao Telegram (o resto funciona igual). Envio: `POST {TELEGRAM_API_URL}/bot{TELEGRAM_TOKEN}/sendMessage` com `{"chat_id", "text"[, "reply_to_message_id"]}`; a resposta do Telegram traz `result.message_id`.

**Atendimento humano** (`/api/atendimento-humano` → `{"fila": [{id, telefone, nome, motivo, prioridade, status}]}` só com os `aberto`):
- Ao abrir (pedido de atendente, emergência, alerta clínico, dor ≥ `dor_alerta`, 2º "não entendi"): manda ao grupo um texto com `#<id>`, telefone, nome (se houver), motivo, a última mensagem do paciente e, se `prioridade` for `alta`, a palavra `ALTA`. Guarda o `message_id`.
- Enquanto o atendimento do telefone estiver `aberto`, o bot **não responde** sozinho (`respostas: []`), exceto regras 1 e 2; cada mensagem do paciente vai ao grupo como `#<id> <nome ou telefone>: <texto>`, em resposta (`reply_to_message_id`) à mensagem de abertura.
- `POST /webhook/telegram` exige header `X-Telegram-Bot-Api-Secret-Token: {TELEGRAM_SEGREDO}` (senão 401). Só aceita updates de `message.chat.id == TELEGRAM_CHAT_ID` (comparados como texto); os outros são ignorados (200, sem efeito).
- Mensagem da equipe que é resposta (`reply_to_message.message_id`) a uma mensagem do atendimento `#id` → o texto vai ao paciente (caixa de saída `tipo: "humano"`, e pela Evolution se configurada).
- Comandos: `/responder <id> <texto>` (o mesmo, sem precisar responder em cima); `/encerrar <id>` → status `encerrado`, o bot volta a responder aquele telefone; `/fila` → o bot manda a lista dos abertos (cada um com `#id`); `/agenda [AAAA-MM-DD]` (padrão: hoje pelo relógio) → manda os agendamentos ativos do dia, uma linha `HH:MM <nome do paciente> — <nome do serviço> (<nome do profissional>)` cada; `/alertas` → manda os alertas `aberto` (seção 24), uma linha `#<id> <tipo> <nome do paciente>: <texto>` cada, ou `Nenhum alerta aberto.`
- Pela equipe [R]: `POST /api/atendimento-humano/{id}/responder {texto}` e `POST /api/atendimento-humano/{id}/encerrar` fazem o mesmo.
- **Avisos à equipe:** agendamento feito pelo chat → `Novo agendamento: DD/MM HH:MM <nome> — <serviço> com <profissional>`; cancelamento pelo chat → texto começando com `Cancelado:` e com `DD/MM HH:MM`; alerta novo (seção 24) → `Alerta <tipo> #<id>: <nome do paciente> — <texto>`.

## 19. Docker / VPS

- `Dockerfile` (imagem oficial `python:3-slim` ou similar, **sem `pip install`**) que copia `atende`, `VERSION`, `src/`, `web/`, `exemplos/` e roda `./atende serve --host 0.0.0.0 --porta 8080 --dados /dados`, com `HEALTHCHECK` em `/api/saude` feito com `python3` (sem `curl`). Sobe sem volume (cria `/dados`).
- `docker-compose.yml` com o serviço `atende`: `build: .`, `restart: unless-stopped`, `env_file: .env`, volume para `/dados`, porta publicada só em `127.0.0.1:8080` (na VPS fica atrás de proxy reverso com HTTPS).
- `.env.exemplo` com todas as variáveis das seções 17, 18 e 21 (`EVOLUTION_URL, EVOLUTION_API_KEY, EVOLUTION_INSTANCIA, WEBHOOK_SEGREDO, PUBLIC_URL, EXERCICIOS_MP4_DIR, TELEGRAM_API_URL, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID, TELEGRAM_SEGREDO`), todas com valor **vazio** (nenhum segredo, nenhuma palavra `http` no arquivo).
- `README.md` com as seções **Deploy na VPS** (subir o compose, proxy HTTPS, webhook da Evolution para `/webhook/evolution/<segredo>` com evento `MESSAGES_UPSERT`, webhook do Telegram com `setWebhook` + `secret_token`, backup diário com `./atende backup` no cron, `PUBLIC_URL` e onde ficam os MP4) e **Como rodar no seu ambiente** (seção do dono: pré-requisitos, congelar, loop/`/goal`, verificação independente — o implementador **não a reescreve**).

## 20. Planos de tratamento [R]

Um plano é o pacote de sessões que o fisioterapeuta prescreve a um paciente.

| Método e rota | Corpo | Resposta |
|---|---|---|
| `POST /api/planos` | `{paciente_id, servico, sessoes_previstas, frequencia_semanal, profissional?, observacao?, servico_avaliacao?}` | 201 com o plano; paciente/serviço/profissional inexistente → 404; `sessoes_previstas` ou `frequencia_semanal` não inteiro ≥ 1 → 422; já existe plano `ativo` do mesmo paciente com o mesmo `servico` → 409 |
| `GET /api/planos[?paciente_id=P]` | — | 200 `{"planos": [plano, ...]}` ordem de `id` |
| `GET /api/planos/{id}` | — | 200 plano; inexistente → 404 |
| `POST /api/planos/{id}/encerrar` | `{motivo}` | 200 plano com `status: "encerrado"`; plano que não está `ativo` → 409 |

Plano = `{id, paciente_id, servico, servico_avaliacao, profissional, sessoes_previstas, frequencia_semanal, observacao, criado_em, status, realizadas, faltas, faltas_seguidas, restantes, ultima_sessao, alerta_abandono, alerta_reavaliacao}`:

- `criado_em` = relógio do processo na criação (`AAAA-MM-DDTHH:MM`); `status` ∈ `ativo, concluido, encerrado`; `servico_avaliacao` padrão `avaliacao` (se existir um serviço com esse id; senão `null` e o plano concluído não gera retorno).
- `realizadas` = agendamentos vinculados com status `realizado`; `faltas` = vinculados com `falta`; `restantes = max(0, sessoes_previstas − realizadas)`; `ultima_sessao` = `inicio` do último `realizado` (ou `null`).
- `faltas_seguidas` = faltas vinculadas depois do último `realizado` (ordem de `inicio`); um `realizado` zera a contagem.
- `realizadas == sessoes_previstas` → `status: "concluido"` na hora da presença, e nasce o retorno da seção 8 (`data = ultima_sessao + reavaliacao_dias`).
- Vínculo: `POST /api/agendamentos` com `plano_id`, ou automático (seção 5). Agendar com `plano_id` de plano não `ativo`, de outro paciente ou de outro serviço → 422; `plano_id` que não existe → 404 (regra geral da seção 5). Agendamento vinculado continua contando mesmo que o plano seja encerrado depois.
- `alerta_abandono` / `alerta_reavaliacao` = `AAAA-MM-DDTHH:MM` do último alerta desse tipo (ou `null`) — seção 24.

## 21. Biblioteca de exercícios e páginas

**Catálogo** (semeado por `clinica.json.exercicios`; mínimo de **12** exercícios no exemplo, cobrindo regiões diferentes; ids obrigatórios do exemplo: `ponte`, `alongamento-isquiotibiais`, `rotacao-ombro-bastao`, `pendulo-codman`, `retracao-cervical`, `gato-camelo`, `agachamento-parede`, `elevacao-calcanhar`, `abducao-quadril-deitado`, `prancha-modificada`, `bird-dog`, `mobilidade-tornozelo`).

| Método e rota | Corpo | Resposta |
|---|---|---|
| `GET /api/exercicios` (público) | — | 200 `{"exercicios": [{id, nome, apelidos, regiao, passos, erros_comuns, cuidados, contraindicacoes, pare_se, ativo, svg}]}` ordem de cadastro, todos (ativos e inativos); `svg` = `true` se `web/exercicios/<id>.svg` existe |
| `POST /api/exercicios` [R] | `{id, nome, apelidos?, regiao, passos, erros_comuns?, cuidados?, contraindicacoes?, pare_se?}` | 201; `id` repetido → 409; `passos` vazio ou `id` fora de `[a-z0-9-]+` → 422 |
| `PUT /api/exercicios/{id}` [R] | parcial | 200 com o exercício; inexistente → 404 |
| `DELETE /api/exercicios/{id}` [R] | — | 200 `{"ativo": false}`: some do chat (regra 9) e as páginas respondem 404; não pode entrar em prescrição nova |

**Páginas** (públicas, sem dado pessoal):
- `GET /exercicios/{id}` → 200 HTML com elemento `id="exercicio"`, o `nome`, os `passos` numerados, `erros_comuns`, `cuidados`, `contraindicacoes`, `pare_se` e `<img src="/exercicios/{id}.svg">` (ou o SVG inline). Exercício inexistente ou inativo → 404. Página existe mesmo sem o arquivo SVG.
- `GET /exercicios/{id}.svg` → 200 com `Content-Type: image/svg+xml` e o conteúdo de `web/exercicios/{id}.svg`; sem arquivo, inexistente ou inativo → 404.
- `GET /exercicios/{id}.mp4` → 200 `Content-Type: video/mp4` com `{EXERCICIOS_MP4_DIR}/{id}.mp4`; sem arquivo → 404. `EXERCICIOS_MP4_DIR` (variável de ambiente) tem padrão `web/exercicios` relativo à raiz do repo.

**SVG animado** — um arquivo `web/exercicios/<id>.svg` por exercício do exemplo (os 12 do fixture), parte da entrega:
- XML válido; raiz `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 400">` (qualquer `viewBox` serve, mas tem de existir); `<title>` em português com o nome do exercício, **filho direto** da raiz `<svg>`.
- Figura humana esquemática (cabeça em círculo, tronco e membros em linhas/paths) fazendo o movimento do exercício em **loop**.
- Animação **só por CSS** dentro de `<style>` no próprio SVG: pelo menos um `@keyframes` e pelo menos um elemento com `animation` (ou `animation-name`) aplicada. `animation-duration` de cada animação ∈ {1s, 2s, 4s} (divisor dos 4 s do MP4, seção 25); `animation-iteration-count: infinite` é permitido. **Sem SMIL** (`<animate>`, `<animateTransform>`, `<animateMotion>`, `<set>`): o render só sabe avançar animação CSS.
- **Sem `<script`**, sem `href`/`xlink:href` que não comece por `#`, sem `url(` que não seja `url(#`, sem `@import`, sem `<image`, sem `<foreignObject`, e nenhuma ocorrência de `http` fora de `http://www.w3.org/` (namespaces).
- Tamanho ≤ 60 KB.
- Nível 4 (humano): abrindo o SVG num navegador, dois quadros em tempos diferentes têm de ser diferentes (a figura se mexe).

Esqueleto de referência (o implementador cria um por exercício, com movimento próprio):
```svg
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 400">
  <title>Ponte</title>
  <style>
    .quadril { transform-origin: 200px 300px; animation: sobe 2s ease-in-out infinite; }
    @keyframes sobe { 0%, 100% { transform: translateY(0); } 50% { transform: translateY(-40px); } }
  </style>
  <rect width="400" height="400" fill="#fff"/>
  <line x1="40" y1="330" x2="360" y2="330" stroke="#999" stroke-width="4"/>
  <circle cx="70" cy="300" r="18" fill="none" stroke="#222" stroke-width="6"/>
  <g class="quadril" fill="none" stroke="#222" stroke-width="8" stroke-linecap="round">
    <path d="M 90 300 L 220 300 L 260 250 L 280 320"/>
  </g>
</svg>
```

## 22. Prescrição de exercícios domiciliares e lembretes

| Método e rota | Corpo | Resposta |
|---|---|---|
| `POST /api/pacientes/{id}/prescricao` [R] | `{itens: [{exercicio, series, repeticoes, vezes_dia, dias: ["seg", ...], observacao?}], lembrete_hora?}` | 201 com a prescrição; substitui a anterior (que fica inativa); paciente inexistente → 404; `itens` vazio, exercício inexistente/inativo, `series`/`repeticoes`/`vezes_dia` não inteiro ≥ 1, `dias` vazio ou com valor fora de `seg..dom`, `lembrete_hora` fora de `HH:MM` → 422 |
| `GET /api/pacientes/{id}/prescricao` [R] | — | 200 prescrição ativa; sem prescrição ativa → 404 |
| `DELETE /api/pacientes/{id}/prescricao` [R] | — | 204; inativa a prescrição e desliga o lembrete |
| `PUT /api/pacientes/{id}/lembrete` [R] | `{lembrete_hora?, lembrete_ativo?}` | 200 `{lembrete_hora, lembrete_ativo}` (a equipe pode desligar ou mudar a hora; ligar continua sendo escolha do paciente, mas a rota aceita `true`) |

Prescrição = `{id, paciente_id, criado_em, inicio, itens: [{exercicio, nome, series, repeticoes, vezes_dia, dias, observacao}], lembrete_hora, lembrete_ativo, ativo}`:
- `inicio` = data (`AAAA-MM-DD`) do relógio do processo na criação; `nome` vem do catálogo.
- `lembrete_hora` e `lembrete_ativo` pertencem ao **paciente** (persistem quando a prescrição é substituída). Todo paciente nasce com `lembrete_ativo: false` e `lembrete_hora = lembrete_hora_padrao` da clínica (é o que `GET .../dados` mostra mesmo sem prescrição); o `lembrete_hora` enviado na prescrição substitui a hora. O paciente liga/desliga pelo chat (regra 7).
- Ao criar, o sistema manda ao paciente (síncrono, `tipo: "prescricao"`, não para `nao_contatar`) um texto com cada item (`- <nome>: <series> x <repeticoes>, <vezes_dia>x ao dia (<dias separados por ", ">)`), o link de cada exercício e a frase `Para receber lembrete diário, responda LEMBRETE e a hora (ex.: LEMBRETE 19:00).`

**Lembrete diário** (em `POST /api/tarefas/rodar`): para cada paciente com prescrição ativa, `lembrete_ativo: true` e não `nao_contatar`: se a hora de `agora` ≥ `lembrete_hora`, o dia da semana de `agora` está nos `dias` de pelo menos um item e ainda não houve mensagem `tipo: "exercicio"` para o paciente na data de `agora` → cria a mensagem `tipo: "exercicio"` com os itens **do dia** (`- <nome>: <series> x <repeticoes>, <vezes_dia>x ao dia` + observação) e a frase `Responda FIZ, NÃO FIZ ou a dor de 0 a 10.` Uma por dia. Dia sem item → nada.

## 23. Adesão e dor

**Registro** (regras 6 e 8 da conversa): um registro por paciente por **dia** (`data` = data do relógio do processo quando a mensagem chegou): `{data, fez, dor, quando}`; `fez` ∈ `true, false, null`; `dor` ∈ `0..10, null`; `quando` = relógio na última alteração. Mensagens no mesmo dia **atualizam** o mesmo registro (último valor de cada campo vence).

`GET /api/pacientes/{id}/adesao?semanas=N` [R] (padrão `N=4`) → 200
```json
{"semanas": [{"inicio": "AAAA-MM-DD", "previstos": 4, "feitos": 2, "adesao_pct": 50.0, "dor_media": 4.0}],
 "registros": [{"data", "fez", "dor", "quando"}]}
```
- Semana = segunda a domingo; `inicio` = a segunda. `semanas` lista, em ordem cronológica, as últimas `N` semanas entre a semana de `inicio` da prescrição ativa e a semana de hoje (vazia sem prescrição ativa). `registros` em ordem de `data`.
- `previstos` = dias da semana que (a) estão nos `dias` de pelo menos um item da prescrição ativa, (b) são ≥ `inicio` da prescrição e (c) são ≤ hoje (relógio do processo), **inclusive hoje**.
- `feitos` = desses dias, os que têm registro com `fez: true`. Registro `fez: true` em dia não previsto não conta.
- `adesao_pct = feitos ÷ previstos × 100`, 1 casa; 0 se `previstos = 0`.
- `dor_media` = média de `dor` dos registros da semana com `dor` não nulo (qualquer dia, previsto ou não), 1 casa; `null` se não houver.
- Exemplo: prescrição criada ter 06/10/2026 com itens em `seg,qua,sex` e `ter,qui`; registros 06/10 `fiz, dor 3`, 07/10 `nao fiz`, 08/10 `fiz, dor 5`; consulta sex 09/10 → semana `2026-10-05`: `previstos 4` (06, 07, 08, 09), `feitos 2`, `adesao_pct 50.0`, `dor_media 4.0`.

`GET /api/adesao` [R] → 200 `{"pacientes": [{paciente_id, nome, adesao_pct, dor_media, ultima_dor}]}` de todos os pacientes com prescrição ativa, ordem de `paciente_id`, valores da semana atual (`ultima_dor` = `dor` do registro mais recente com dor, ou `null`).

**Dor forte e sinais de alerta:** regra 2 (palavras) e regra 8 (`dor ≥ dor_alerta`) abrem atendimento humano `alta` (seção 18) e nunca respondem com orientação clínica.

## 24. Alertas à equipe

Calculados em `POST /api/tarefas/rodar` (com o `agora` da rodada), idempotentes; cada um vai ao Telegram ao nascer (seção 18).

| `tipo` | Quando | Texto |
|---|---|---|
| `abandono` | plano `ativo` com `faltas_seguidas ≥ abandono_faltas` e `alerta_abandono` nulo **ou** anterior ao `inicio` do último agendamento `realizado` do plano (ou seja, um alerta por sequência de faltas; a sequência recomeça depois de um `realizado`) | `<nome>: <faltas_seguidas> faltas seguidas no plano de <nome do serviço>` |
| `reavaliacao` | plano `ativo` com `restantes ≤ reavaliacao_sessoes` e `alerta_reavaliacao` nulo (um por plano, inclusive quando o plano já nasce com poucas sessões) | `<nome>: faltam <restantes> sessões do plano de <nome do serviço> — agendar reavaliação` |

`GET /api/alertas` [R] → 200 `{"alertas": [{id, tipo, paciente_id, nome, plano_id, texto, quando, status}]}` só os `aberto`, ordem de `id`. `POST /api/alertas/{id}/resolver` [R] → 200 `{status: "resolvido"}`; inexistente → 404. `alertas` em `tarefas/rodar` = quantos nasceram na rodada.

## 25. Vídeo MP4 do exercício (build do humano, fora do pytest e do loop)

`tools/render-exercicios [--so <id>] [--saida DIR]` (Python 3, biblioteca padrão; chama `npx hyperframes` e `ffprobe`) gera `web/exercicios/<id>.mp4` (ou em `--saida`) a partir de cada `web/exercicios/<id>.svg`:

1. Cria uma pasta temporária com `index.html` = composição HyperFrames **só CSS** (sem GSAP, sem `<script>`, sem referência externa): `<div id="root" data-composition-id="exercicio" data-start="0" data-width="720" data-height="720" data-duration="4">` contendo o SVG inline (`#root svg { position:absolute; inset:0; width:100%; height:100% }`, `body { margin:0; background:#fff }`). A animação CSS do SVG é avançada pelo adaptador `css` do HyperFrames (por isso a seção 21 proíbe SMIL e exige durações de 1, 2 ou 4 s).
2. Roda `npx hyperframes render <pasta> --output <destino>.mp4 --quality looks --fps 30` (≈ 4 s, 720×720, sem áudio).
3. Confere com `ffprobe -v error -show_entries format=duration:stream=width,height -of default=nw=1`: duração entre 3,9 e 4,1 s e 720×720; senão sai com código 1 e diz qual exercício falhou.
4. Imprime uma linha por exercício (`ok <id> <duração>s` ou `falhou <id> <motivo>`); código 0 só se todos passaram.

Requisitos (do humano, não do loop): Node ≥ 22, FFmpeg, Chromium (o `npx hyperframes` baixa o pacote na primeira vez — **precisa de rede**, por isso o agente da execução longa não roda este passo). `verificar-independente.py` renderiza um exercício se o HyperFrames estiver disponível; senão imprime `pulado`. Os MP4 não entram no Git (`.gitignore`); na VPS, rode o `tools/render-exercicios` uma vez (ou copie os arquivos) para `EXERCICIOS_MP4_DIR`.
