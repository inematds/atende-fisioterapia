Você está num ciclo de uma execução longa no repo /home/nmaldaner/projetos/atende-fisioterapia.

RESULTADO: `./atende` (Python 3, só biblioteca padrão; código em `src/`, páginas e SVGs em `web/`, utilitário de build em `tools/`) implementa docs/ESPECIFICACAO.md por inteiro — atendimento de uma clínica de fisioterapia.

ANTES DE AGIR: leia longrun/2026-10-05-fisio-v1/goal.md → state.md → plan.md → canal.md → últimas linhas de progress.md e failures.md. Na primeira vez, leia docs/ESPECIFICACAO.md inteiro (inclusive o bloco "O que muda em relação ao atende-clinica"), tests/conftest.py e tests/fixtures/clinica.json. O projeto irmão ~/projetos/atende-clinica tem uma implementação do molde (src/, web/) que você pode reaproveitar onde a spec for igual — mas a fonte da verdade é a spec deste repo.

NESTE CICLO: escolha a próxima ação útil (comece pela base: `./atende serve` imprimindo `PORTA=<n>`, SQLite em --dados, auth; depois agenda → conversa → confirmação/espera → planos e alertas → biblioteca de exercícios, páginas e os 12 SVGs (`web/exercicios/<id>.svg`, só animação CSS, sem SMIL, sem script) → prescrição, lembrete, registro de adesão/dor e alerta clínico → campanhas → LGPD → raiox → cadastros/bloqueios/backup → Evolution (sendText e sendMedia) → Telegram (inclusive /alertas) → Docker/README/.env.exemplo → página /equipe → `tools/render-exercicios` (escrever conforme a seção 25; NÃO executar, precisa de rede)), implemente, rode `python3 -m pytest -q tests/` (leva alguns minutos). Leia só o fim da saída (`| tail -30`); saída longa vai para arquivo.

AO TERMINAR O CICLO (obrigatório):
- reescreva state.md (Funciona / Falta / Como retomar) e plan.md (próximos 3 passos);
- acrescente 1 linha em progress.md: data-hora, o que mudou, resultado do pytest (N passed / N failed);
- se algo deu errado, 1 linha em failures.md: erro → tentativa → resultado;
- decisões de design em decisions.md; fatos e armadilhas novos em canal.md (só acrescentar);
- quando `python3 -m pytest -q tests/` passar inteiro (98 passed) E `bash longrun/2026-10-05-fisio-v1/verificar-limites.sh` imprimir LIMITES OK, escreva "concluído" na primeira linha de "## Funciona" do state.md.

SE UM TESTE CONTRADIZ A ESPECIFICAÇÃO: não altere o teste nem a spec. Registre em failures.md (teste, trecho da spec, o conflito) e siga com os outros itens; isso é portão humano.

INTEGRAÇÕES: Evolution e Telegram só pelas variáveis de ambiente da spec; teste só contra o servidor falso dos testes. Nunca chame api.telegram.org nem uma Evolution real, nunca escreva URL externa no código (a única exceção é o namespace `http://www.w3.org/2000/svg` dentro dos SVGs). O bot nunca dá orientação clínica: fora do FAQ e da prescrição, humano.

RESTRIÇÕES: não altere tests/, pytest.ini, docs/, goal.md, hash-congelado.txt, congelar.sh, verificar-*, loop.env, prompt.md. Não reescreva a seção "Como rodar no seu ambiente" do README.md (acrescente as suas). Só biblioteca padrão do Python 3 (`python3`, não `python`). Nenhuma API, nenhuma rede externa, nenhuma chave, nenhum `npx`/`npm`/`docker`. Servidor só em 127.0.0.1. Não use `pkill -f`; mate só o PID que você subiu. Não faça commit (o loop externo faz).
