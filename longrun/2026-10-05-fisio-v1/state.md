# Estado — atualizado 2026-10-19 13:50

## Funciona
- Base executável `./atende serve`: primeira linha PORTA, SQLite em --dados, relógio ATENDE_AGORA, autenticação antes do corpo e fila de conexões ampliada.
- Reaproveitados src/ e web/ do atende-clinica, sem dependências externas. Todos os testes de agenda passaram, inclusive concorrência e presença; presença repetida agora dá 409.
- FAQ, fluxo básico do chat, emergência, sinais clínicos por palavras inteiras, confirmação e espera persistidas; cadastros e bloqueios básicos; campanhas incluindo depoimento COFFITO; transporte sendText e atendimento Telegram básico verificados pelos testes locais.
- `python3 -m pytest -q tests/`: **56 passed / 42 failed**, 26,90 s. Log completo: `longrun/2026-10-05-fisio-v1/pytest-ciclo-1.log`.
- `bash longrun/2026-10-05-fisio-v1/verificar-limites.sh`: **LIMITES OK**, hash 381b6510e90832d5, 98 testes.

## Falta
- Planos: API, vínculo automático/expresso na agenda, contagens, conclusão, retorno de avaliação, alertas e /alertas Telegram. A agenda tem coluna plano_id mas ainda rejeita plano informado (404).
- Biblioteca: exercícios já semeados em catalogo, mas faltam CRUD, rotas públicas, páginas, 12 SVGs e MP4; regras de explicação e sendMedia.
- Prescrição, lembretes opt-in, registro de adesão/dor, agregados e extensão LGPD/Raio-X. Defaults da clínica inseridos; preferências de lembrete do paciente ainda faltam.
- /equipe ainda não existe: web/ mantém interface /recepcao do molde; adaptar em etapa própria. Docker, compose, .env.exemplo, seção Deploy na VPS e tools/render-exercicios faltam.
- Testes de persistência/semente/backup ainda falham nos recursos novos; não considerar essas funcionalidades integralmente aceitas.
- Sem conflitos identificados entre teste e spec neste ciclo. Não marcar concluído.

## Como retomar
1. Ler goal → state → plan → canal → fim de progress/failures. Especificação inteira e conftest/fixture lidos neste ciclo.
2. Implementar planos em módulo próprio, ligar à agenda/presença e depois às tarefas/alertas. Presença não deve voltar a gerar retorno por serviço.
3. Rodar `python3 -m pytest -q tests/ > /tmp/fisio-pytest.log 2>&1; tail -30 /tmp/fisio-pytest.log` e `bash longrun/2026-10-05-fisio-v1/verificar-limites.sh`.
4. Atualizar registros; não fazer commit, não executar render, não usar rede externa.
