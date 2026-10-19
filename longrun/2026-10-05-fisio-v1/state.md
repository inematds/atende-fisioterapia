# Estado — atualizado 2026-10-19 14:02

## Funciona
- Base serve/SQLite/auth, agenda concorrente, conversa/FAQ/emergência/alertas clínicos, confirmação/espera, cadastros/bloqueios/backup, campanhas, planos e alertas de abandono/reavaliação, indicadores Raio-X e transportes opcionais.
- Biblioteca persistente com CRUD, páginas públicas e 12 SVGs CSS; recursos MP4 locais. Revisão clínica e visual no navegador continuam humanas.
- Prescrição: criação validada, substituição mantendo histórico inativo e preferências do paciente, GET/DELETE, envio síncrono e bloqueio nao_contatar. Migração de pacientes existentes; pacientes novos recebem hora padrão e opt-in falso.
- Lembrete opt-in por chat/API, validação de hora original, itens do dia e um envio por data; caixa de saída e histórico usam agora da rodada. Regras 6–8 registram adesão/dor no dia do processo; dor forte abre humano alta com aviso ao Telegram.
- Adesão semanal/geral calculada da prescrição ativa, registros persistentes com atualização independente de fez/dor. LGPD exporta prescrição/registros/preferências; remoção inativa prescrição, desliga lembrete e apaga registros.
- VERSION 0.4.0. Suíte final: **89 passed / 9 failed**, 49,19 s; log `longrun/2026-10-05-fisio-v1/pytest-ciclo-4.log` (ganho de 12 testes).
- **LIMITES OK**, hash 381b6510e90832d5, 98 testes. Validação local adicional OK: reinício, preservação de opt-in/hora na substituição, itens inválidos, semanas muito grandes, idempotência e timestamp do histórico. `git diff --check -- src VERSION FALHAS.md` OK.

## Falta
- Regra 9: explicação somente de exercício prescrito, nomes/apelidos normalizados, termo mais longo e listagem por palavra exercício. Quatro falhas cobrem conversa e Evolution sendMedia/fallback sendText.
- /equipe com ações reais (1 falha); interface /recepcao ainda vem do molde.
- Dockerfile, compose, .env.exemplo e seção Deploy na VPS no README (4 falhas). Preservar seção do dono.
- Escrever tools/render-exercicios conforme §25; NÃO executar. Não está coberto pela suíte de 98 testes, mas faz parte do resultado.
- Nenhum conflito teste/especificação identificado. Resultado geral ainda não concluído.

## Como retomar
1. Ler goal → state → plan → canal → fins progress/failures. Especificação inteira, conftest e fixture lidos neste ciclo.
2. Implementar regra 9 e sendMedia; evitar duplicação entre enviar(), conversar() e evolution(). Prescrição e lembrete já têm envio síncrono pelo transporte existente.
3. Completar equipe e entrega/render, rodar suíte inteira e verificar-limites.sh. Só marcar concluído com 98 passed e LIMITES OK, mantendo toda a spec implementada.
4. Atualizar registros; sem commits, rede externa, render, npm/npx ou Docker. Logs ciclo-4.log, loop.log e teste-final.log pertencem ao loop externo; não editar.
