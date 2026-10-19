# Estado — atualizado 2026-10-19 14:08

## Funciona
- Base serve/SQLite/auth, agenda concorrente, conversa/FAQ/emergência/alertas clínicos, confirmação/espera, cadastros/bloqueios/backup, campanhas, planos e alertas de abandono/reavaliação, indicadores Raio-X e transportes opcionais.
- Biblioteca persistente com CRUD, páginas públicas e 12 SVGs CSS; recursos MP4 locais. Revisão clínica e visual no navegador continuam humanas.
- Prescrição: criação validada, substituição mantendo histórico inativo e preferências do paciente, GET/DELETE, envio síncrono e bloqueio nao_contatar. Migração de pacientes existentes; pacientes novos recebem hora padrão e opt-in falso.
- Lembrete opt-in por chat/API, validação de hora original, itens do dia e um envio por data; caixa de saída e histórico usam agora da rodada. Regras 6–8 registram adesão/dor no dia do processo; dor forte abre humano alta com aviso ao Telegram.
- Adesão semanal/geral calculada da prescrição ativa, registros persistentes com atualização independente de fez/dor. LGPD exporta prescrição/registros/preferências; remoção inativa prescrição, desliga lembrete e apaga registros.
- Regra 9: explica somente exercício ativo prescrito, normaliza nomes/apelidos, escolhe termo mais longo (empate por catálogo) e lista os prescritos. Explicação gera saída própria; não vira pendência de dor.
- Evolution envia explicação por sendMedia quando há MP4 local e PUBLIC_URL, ou sendText; ID do exercício persistido permite reenvio após reinício. Webhook e histórico não duplicam a resposta; nao_contatar bloqueia a saída.
- VERSION 0.5.0. Suíte: **93 passed / 5 failed**, 38,23 s; log `longrun/2026-10-05-fisio-v1/pytest-ciclo-5.log` (ganho de 4 testes).
- **LIMITES OK**, hash 381b6510e90832d5, 98 testes. Validação complementar `validar-explicacao.py` OK: reenvio após reinício, histórico único, ausência de pendência, prioridade/empate de termos, inativo e opt-out. `git diff --check -- src VERSION` OK.

## Falta
- /equipe com ações reais (1 falha); interface /recepcao ainda vem do molde.
- Dockerfile, compose, .env.exemplo e seção Deploy na VPS no README (4 falhas). Preservar seção do dono.
- Escrever tools/render-exercicios conforme §25; NÃO executar. Não está coberto pela suíte de 98 testes, mas faz parte do resultado.
- Nenhum conflito teste/especificação identificado. Resultado geral ainda não concluído.

## Como retomar
1. Ler goal → state → plan → canal → fins progress/failures. Especificação inteira, conftest e fixture lidos neste ciclo.
2. Implementar /equipe com ações reais nas rotas existentes; /recepcao ainda é do molde. Consultar §13–15 e §20–24.
3. Completar Docker/compose/env/README e escrever tools/render-exercicios (§25) sem executar. Preservar seção do dono no README.
4. Rodar suíte inteira e limites; só marcar concluído com 98 passed e LIMITES OK e toda a spec implementada. Atualizar registros; sem commits, rede externa, render, npm/npx ou Docker. Logs ciclo-5.log, loop.log e teste-final.log pertencem ao loop externo; não editar.
