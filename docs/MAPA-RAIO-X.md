# Como o Raio-X de Margem alimenta este projeto

Fonte: `~/projetos/raio-x-margem` (pacote `setores/clinica.js`, que herda de `setores/servicos.js`; receita `docs/modulos/servicos-agenda.md`; análise `docs/setores/servicos.md`; pesquisa `docs/setores/servicos-pesquisa-2026-10.md`). Perfil: clínica, com o que o pacote diz da fisioterapia — `atendimentos_mes_recorrente` ("tratamento contínuo (fisio, psicologia) pode passar de 2") e o alerta do Caçador para CNAE 8650-0/04 ("promoção e preço fora do consultório vedados — COFFITO 424/2013").

## Vazamentos da clínica × o que o atende-fisioterapia ataca

| Vazamento (id no Raio-X) | Entradas que o sistema mede | Peça no v1 | Seção da spec |
|---|---|---|---|
| `faltas` — falta sem aviso (nº 1: bem gerida 5–12 %, média ~25 %, fornecedor) | `atendimentos_mes`, `falta_pct` | confirmação automática 48 h + "1/2" + lista de espera; na fisio, **faltas seguidas num plano** viram alerta de abandono à equipe | 7, 8, 20, 24 |
| `retencao` — paciente que não volta (`clientes_novos_mes`, `retorno_atual_pct`, `atendimentos_mes_recorrente`) | os três | retorno (reavaliação) ao concluir o plano; `atendimentos_mes_recorrente` = sessões ÷ pacientes atendidos no mês | 8, 10, 20 |
| `orcamentos` — tratamento indicado que não começa (`orcamentos_mes`, `aprovacao_atual_pct`) | os dois | plano de tratamento = orçamento apresentado; "aprovado" = plano com ≥ 1 sessão realizada; alerta de reavaliação quando o pacote acaba | 10, 20, 24 |
| `ociosidade` — horário que nunca foi agendado (`ocupacao_pct`) | `ocupacao_pct` | agenda pelo chat, horários públicos, lista de espera | 3, 5, 6, 7 |
| `whatsapp_manual` — recepção marcando à mão (`horas_agenda_manual_semana`) | — (premissa, não medida) | agendamento pelo chat + FAQ + fila humana + Telegram da equipe | 6, 18 |
| `sem_agenda_online` | — | horários públicos + chat web | 5, 6, 13 |
| `fidelidade` / plano recorrente, `cartao`, `antecipacao`, `juros` | — | **fora do v1** (precisa de PSP; `cobranca`) | 12 |
| `glosa` | — | **fora** — não é atendimento, é faturamento | 12 |
| `anuncios` | — | fora; campanhas do v1 são de serviço, não anúncio pago | 9 |

Premissas sem número no Raio-X (não inventar): quanto a adesão domiciliar muda alta/resultado; quantas faltas seguidas são abandono (o kit usa 2 como padrão ajustável); impacto do lembrete de exercício. São hipóteses a medir com os registros do próprio sistema (adesão e dor por semana), não dados de mercado.

## Regras que viraram trava testável

- **COFFITO 424/2013** (pesquisa §9): art. 40, I (preço fora do local) → código `preco`; "promoção" (leitura do CREFITO-9) → `promocao`; art. 39 (gratuito/ínfimo) → `gratuito`; art. 10, V (imagem/carta de agradecimento para autopromoção) → `depoimento`; promessa de resultado e "melhor fisioterapeuta" → `promessa_resultado`, `melhor_profissional` (seção 9).
- **LGPD art. 11**: dado de saúde é sensível — confirmação, retorno, prescrição e lembrete de exercício sob tutela da saúde (II, f); campanha só com consentimento específico (I); registros de adesão e dor são apagados na exclusão (seções 8, 9, 11). Interpretação, não texto da ANPD (pesquisa §11 e implicação 10).
- **Lembrete não é propaganda** (receita `servicos-agenda.md`, "Cuidados"): mensagens de confirmação, retorno, prescrição e exercício nunca trazem preço ou promoção.

## Volta para o Raio-X

`GET /api/raiox?mes=` e `./atende raiox --acompanhamento` gravam no arquivo do Painel de Recuperação (`app/painel-motor.js`, formato `acompanhamento`) os ids reais de `setores/clinica.js`: `atendimentos_mes`, `falta_pct`, `ocupacao_pct`, `clientes_novos_mes`, `retorno_atual_pct`, `atendimentos_mes_recorrente`, `orcamentos_mes`, `aprovacao_atual_pct`, com `obs: "atende-fisioterapia"`. O resto (`ticket_medio`, `margem_contrib_pct`, `fat_convenio`, `glosa_pct`…) fica como o implantador preencheu.
