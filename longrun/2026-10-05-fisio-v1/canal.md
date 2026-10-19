# Canal — fisio-v1 (só acrescentar; nunca reescrever)

Conhecimento do projeto que a compactação perde: fatos descobertos, aprendizados, glossário, armadilhas, onde estão as coisas.
Não é estado da tarefa (isso vai em state/plan/progress). Preencha cedo — o hook avisa na faixa 1 (~50% do contexto).

Formato: `- AAAA-MM-DD HH:MM · fato|aprendizado|glossário|armadilha · texto`

- 2026-10-19 13:50 · fato · Base importada de atende-clinica/src e web; catalogo é JSON em SQLite com ordem rowid. Config semeia catálogos uma vez, incluindo exercícios. Testes completos: 56 passed / 42 failed.
- 2026-10-19 13:50 · armadilha · O molde gerava retorno por servico.retorno_dias: removido. Agora retorno deverá nascer exclusivamente da conclusão de plano. Não copiar essa regra antiga de volta.
- 2026-10-19 13:50 · fato · Integracoes só lê URLs do ambiente; testes higienizam ambiente e usam servidor falso. Nenhuma chamada externa feita. UI /recepcao ainda é provisória; /equipe precisa ser implementada.
