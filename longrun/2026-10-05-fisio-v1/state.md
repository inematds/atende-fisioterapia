# Estado — atualizado 2026-10-19 13:54

## Funciona
- Base `./atende serve`, SQLite, auth, agenda concorrente, conversa básica, FAQ, emergência/sinais clínicos, confirmação e espera persistidas, cadastros, campanhas e transportes opcionais do ciclo anterior.
- Planos: criação/validação/listagem/encerramento, um ativo por paciente/serviço, vínculo explícito ou automático na agenda, contagem por início das sessões, conclusão e retorno de reavaliação. Planos incluídos na exportação de dados e encerrados na anonimização.
- Alertas de abandono e reavaliação persistidos, resolução, avisos ao Telegram e comando /alertas. Marcador da última sessão realizada impede duplicação por sequência mesmo com relógio anterior às presenças.
- Raio-X: recorrência, orçamentos e aprovação; testes HTTP/CLI de indicadores aprovados. VERSION 0.2.0.
- Suíte completa: **70 passed / 28 failed**, 34,95 s; log `longrun/2026-10-05-fisio-v1/pytest-ciclo-2.log`. Nenhuma falha nos testes de planos ou lembretes/retorno.
- Checagem local adicional: duas sequências de abandono, repetição da rodada e reinício no mesmo banco sem duplicar alertas: OK.
- Verificação de limites: **LIMITES OK**, hash 381b6510e90832d5, 98 testes, escopo válido. `git diff --check` sem erros.

## Falta
- Biblioteca: CRUD, rotas públicas, páginas e os 12 SVGs CSS. Catálogo já semeado, mas ainda sem API.
- Prescrição, preferências/lembretes opt-in, registro de adesão/dor, alertas por dor e agregados; completar LGPD com prescrição/registros e preferências.
- Explicação de exercício prescrito e Evolution sendMedia/MP4.
- Página /equipe (a interface /recepcao ainda é do molde), Docker/compose/env/README e tools/render-exercicios (escrever, NÃO executar).
- As 28 falhas restantes se concentram nesses recursos ausentes. Nenhum conflito entre testes e especificação identificado. Não marcar concluído.

## Como retomar
1. Ler goal → state → plan → canal → fins de progress/failures. Especificação inteira, conftest e fixture já lidos.
2. Implementar biblioteca/exercícios (seção 21) e depois prescrição/adesão (22–23), usando `src/planos.py` como módulo de domínio independente. Não voltar ao retorno por serviço do molde.
3. Rodar `python3 -m pytest -q tests/` com saída em arquivo e ler só as últimas 30 linhas; depois verificar-limites.sh.
4. Atualizar registros; sem commits, rede externa, render, npm/npx ou Docker. Loop externo cuida de commits; não alterar seus logs.
