# Falhas (só acrescentar; ao fim, a menor correção vira linha no FALHAS.md do projeto)

| data | o que quebrou | tentativa | resultado | prompt \| infra |
|---|---|---|---|---|
| 2026-10-19 13:50 | 42 testes falham: recursos específicos da fisioterapia e entrega ausentes | importar base e adaptar presença, sinais clínicos e campanhas | 56 passed; implementar planos, exercícios, prescrição e entrega nos próximos ciclos; nenhum conflito de contrato identificado | infra |
| 2026-10-19 13:54 | 42 falhas anteriores, planos e recursos domiciliares ausentes → implementar planos/alertas/retorno e indicadores → 70 passed / 28 failed; restantes em biblioteca, prescrição, dor, páginas e entrega; nenhum conflito de contrato | implementação incremental | avanço de 14 testes | infra |
| 2026-10-19 13:58 | 28 falhas anteriores → implementar biblioteca/páginas/SVG/MP4 → 77 passed / 21 failed; CRUD só falha na etapa de prescrição ainda ausente, sem conflito de contrato | implementação incremental | avanço de 7 testes | infra |
| 2026-10-19 13:58 | Leitura inicial tentou src/servidor.py inexistente → consultar rg --files e ler src/server.py → leitura corrigida, sem alteração de código | corrigir caminho | resolvido | prompt |
| 2026-10-19 14:02 | 21 falhas anteriores → implementar prescrição, lembrete opt-in, registros/adesão/dor e LGPD → 89 passed / 9 failed; restantes: regra 9/sendMedia, /equipe e entrega; nenhum conflito com a especificação | implementação incremental | avanço de 12 testes; LIMITES OK | infra |
| 2026-10-19 14:08 | 9 falhas anteriores → implementar regra 9 e transporte de explicação → 93 passed / 5 failed; restantes /equipe e entrega, sem conflito com a especificação | implementação incremental | avanço de 4 testes; LIMITES OK | infra |
| 2026-10-19 14:08 | tail -12 com múltiplos arquivos foi rejeitado na leitura inicial → usar tail -n 12 → leitura corrigida | corrigir sintaxe | resolvido | prompt |
