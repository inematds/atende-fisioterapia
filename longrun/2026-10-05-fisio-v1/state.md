# Estado — atualizado 2026-10-19 13:58

## Funciona
- Base `./atende serve`, SQLite, auth, agenda concorrente, conversa básica, FAQ, emergência/sinais clínicos, confirmação e espera persistidas, cadastros, campanhas e transportes opcionais.
- Planos: criação/validação/listagem/encerramento, vínculo na agenda, presença, conclusão, retorno de reavaliação e alertas persistidos de abandono/reavaliação. Telegram /alertas e indicadores Raio-X ampliados.
- Biblioteca: API pública de listagem, criação/edição/inativação autenticadas, validação dos campos e persistência no catálogo SQLite. Páginas públicas com textos escapados e todos os campos, 404 para inativos/inexistentes, SVG local e MP4 de EXERCICIOS_MP4_DIR (padrão web/exercicios).
- Os 12 SVGs obrigatórios foram escritos, com 12 estilos próprios, figuras esquemáticas, animações CSS de 2/4 segundos e pausa por prefers-reduced-motion. Página responsiva em web/exercicio.html, estilos em web/exercicio.css. VERSION 0.3.0.
- Suíte completa: **77 passed / 21 failed**, 32,41 s; log `longrun/2026-10-05-fisio-v1/pytest-ciclo-3.log`. Ganho de 7 testes sobre o ciclo anterior.
- Verificação de limites: **LIMITES OK**, hash 381b6510e90832d5, 98 testes. Verificação adicional local: persistência de exercício novo após reinício, escape HTML, inativação, rejeição de caminhos e XML/12 estilos distintos: OK.
- `git diff --check -- src web VERSION`: OK. A checagem global apontou espaço final no teste-final.log do loop externo; arquivo preservado.

## Falta
- Prescrição, preferências/lembretes opt-in, registro de adesão/dor, alertas por dor e agregados; completar LGPD com prescrição/registros e preferências.
- Explicação de exercício prescrito e Evolution sendMedia/MP4 (a rota pública do MP4 já funciona).
- Página /equipe (a interface /recepcao ainda é do molde), Docker/compose/env/README e tools/render-exercicios (escrever, NÃO executar).
- O teste biblioteca_crud avança por todo o CRUD e falha na validação final de prescrição inativa, pois a rota de prescrição ainda não existe. Não criar stub; implementar a seção 22 inteira.
- Revisão clínica e movimento visual dos SVGs no navegador continuam como validação humana nível 4; neste ciclo só foram validados XML/CSS, recursos HTTP e regras estruturais.
- Nenhum conflito entre testes e especificação identificado. Não marcar concluído.

## Como retomar
1. Ler goal → state → plan → canal → fins de progress/failures. Especificação inteira, conftest e fixture lidos neste ciclo.
2. Implementar prescrição/adesão (seções 22–23), preferências no paciente e regras 6–9 da conversa, usando src/exercicios.py para consultar o catálogo. Depois completar LGPD e sendMedia sem duplicar saída no webhook.
3. Rodar `python3 -m pytest -q tests/` com saída em arquivo e ler só as últimas 30 linhas; depois verificar-limites.sh.
4. Atualizar registros; sem commits, rede externa, render, npm/npx ou Docker. Loop externo cuida de commits; não alterar seus logs.
