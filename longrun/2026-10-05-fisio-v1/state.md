# Estado — atualizado 2026-10-19 14:11

## Funciona
- Base serve/SQLite/auth, agenda concorrente, conversa/FAQ/emergência/alertas clínicos, confirmação/espera, cadastros/bloqueios/backup, campanhas, planos e alertas de abandono/reavaliação, indicadores Raio-X e transportes opcionais.
- Biblioteca persistente com CRUD, páginas públicas e 12 SVGs CSS; recursos MP4 locais. Revisão clínica e visual no navegador continuam humanas.
- Prescrição: criação validada, substituição mantendo histórico inativo e preferências do paciente, GET/DELETE, envio síncrono e bloqueio nao_contatar. Migração de pacientes existentes; pacientes novos recebem hora padrão e opt-in falso.
- Lembrete opt-in por chat/API, validação de hora original, itens do dia e um envio por data; caixa de saída e histórico usam agora da rodada. Regras 6–8 registram adesão/dor no dia do processo; dor forte abre humano alta com aviso ao Telegram.
- Adesão semanal/geral calculada da prescrição ativa, registros persistentes com atualização independente de fez/dor. LGPD exporta prescrição/registros/preferências; remoção inativa prescrição, desliga lembrete e apaga registros.
- Regra 9: explica somente exercício ativo prescrito, normaliza nomes/apelidos, escolhe termo mais longo (empate por catálogo) e lista os prescritos. Explicação gera saída própria; não vira pendência de dor.
- Evolution envia explicação por sendMedia quando há MP4 local e PUBLIC_URL, ou sendText; ID do exercício persistido permite reenvio após reinício. Webhook e histórico não duplicam a resposta; nao_contatar bloqueia a saída.
- Entrega §19: Dockerfile Python padrão com HEALTHCHECK, compose com dados/backups persistentes e vídeos montados somente para leitura, .env.exemplo com 10 variáveis vazias, .dockerignore e README operacional. Seção do dono preservada byte a byte. Build Docker não executado (restrição do ciclo).
- VERSION 0.6.0. Suíte completa: **97 passed / 1 failed**, 37,40 s; log `longrun/2026-10-05-fisio-v1/pytest-ciclo-6.log`. Única falha: test_paginas, /equipe responde 401.
- **LIMITES OK**, hash 381b6510e90832d5, 98 testes; git diff --check OK. Sem chamadas externas, Docker, render ou commit.

## Falta
- /equipe pública, dados autenticados e ações reais (única falha); /recepcao ainda vem do molde.
- Escrever tools/render-exercicios conforme §25; NÃO executar. Não está coberto pela suíte de 98 testes, mas faz parte do resultado.
- Atualizar os avisos de pendência no README quando equipe/renderizador forem implementados.
- Revisão visual/clínica e build Docker continuam sendo validação humana de nível 4. Nenhum conflito teste/especificação identificado.

## Como retomar
1. Ler goal → state → plan → canal → fins progress/failures. Especificação inteira, conftest e fixture lidos neste ciclo.
2. Implementar /equipe conforme §13–15 e §20–24: rota pública e operações autenticadas nas APIs existentes. Não basta adicionar os IDs ao HTML.
3. Escrever tools/render-exercicios (§25), sem executar; remover os avisos de pendência correspondentes no README.
4. Rodar suíte inteira e limites; só marcar concluído com 98 passed, LIMITES OK e toda a spec implementada. Atualizar registros; sem commits nem rede externa. ciclo-6.log, loop.log e teste-final.log pertencem ao loop externo; não editar.
