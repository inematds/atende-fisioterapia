# Canal — fisio-v1 (só acrescentar; nunca reescrever)

Conhecimento do projeto que a compactação perde: fatos descobertos, aprendizados, glossário, armadilhas, onde estão as coisas.
Não é estado da tarefa (isso vai em state/plan/progress). Preencha cedo — o hook avisa na faixa 1 (~50% do contexto).

Formato: `- AAAA-MM-DD HH:MM · fato|aprendizado|glossário|armadilha · texto`

- 2026-10-19 13:50 · fato · Base importada de atende-clinica/src e web; catalogo é JSON em SQLite com ordem rowid. Config semeia catálogos uma vez, incluindo exercícios. Testes completos: 56 passed / 42 failed.
- 2026-10-19 13:50 · armadilha · O molde gerava retorno por servico.retorno_dias: removido. Agora retorno deverá nascer exclusivamente da conclusão de plano. Não copiar essa regra antiga de volta.
- 2026-10-19 13:50 · fato · Integracoes só lê URLs do ambiente; testes higienizam ambiente e usam servidor falso. Nenhuma chamada externa feita. UI /recepcao ainda é provisória; /equipe precisa ser implementada.
- 2026-10-19 13:54 · fato · src/planos.py cria tabelas planos/alertas no início de Clinica; contagens são consultas à agenda. Retorno usa tabela retornos já criada por conversa.iniciar. Novas rotas passam pelo mesmo lock/transação/auth. Suíte: 70 passed / 28 failed.
- 2026-10-19 13:54 · armadilha · Presenças podem ter início futuro frente a ATENDE_AGORA. Timestamp do alerta isolado não identifica uma sequência já notificada; abandono_ultima_sessao guarda a sequência e não aparece na API. Checado com duas sequências e reinício.
- 2026-10-19 13:58 · fato · src/exercicios.py oferece listar/obter/salvar/pagina/recurso; id validado antes de montar caminhos, catálogo semeado existente reaproveitado. Template em web/exercicio.html e 12 SVGs em web/exercicios. Testes completos: 77 passed / 21 failed.
- 2026-10-19 13:58 · armadilha · test_biblioteca_crud inclui ao final prescrição de exercício inativo; ainda falha 404 porque prescrição não existe, embora operações do CRUD passem. Não alterar teste nem simular rota; implementar seção 22.
- 2026-10-19 13:58 · fato · Apenas validação estrutural e HTTP dos SVGs foi executada; revisão clínica e captura de quadros no navegador ficam para nível 4. CSS d anima pontos com apoios fixos em ponte/gato/agachamento/prancha/bird-dog.
- 2026-10-19 14:02 · fato · src/prescricoes.py concentra prescrição, preferências, lembretes, registros e adesão; inicialização migra pacientes existentes e cria prescricoes/registros. obter retorna None sem ativa; rota GET transforma em 404, LGPD mantém null.
- 2026-10-19 14:02 · armadilha · Pendência de exercício é ausência de dor na data da mensagem; registro da resposta pertence ao dia do relógio do processo. Não usar respondida isoladamente nem trocar data da resposta pela data do lembrete.
- 2026-10-19 14:02 · fato · Integração futura de explicação deve evitar envio duplo: conversar registra histórico e evolution envia toda resposta; enviar também entrega imediatamente. Prescrição/lembrete já usam entregar e seus reenvios funcionam pelo transporte existente.
- 2026-10-19 14:02 · fato · Final do ciclo 4: 89 passed / 9 failed (49,19 s), LIMITES OK. Nº semanas arbitrariamente grande é limitado às semanas disponíveis antes de subtrair datas; preferência e histórico de lembrete conferidos após reinício em validação local adicional.
