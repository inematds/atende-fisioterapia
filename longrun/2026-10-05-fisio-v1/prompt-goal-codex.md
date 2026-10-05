/goal
RESULTADO: `./atende` (Python 3, só biblioteca padrão; `src/` + `web/` + `tools/`) implementa docs/ESPECIFICACAO.md por inteiro — atendimento de uma clínica de fisioterapia com planos de tratamento, exercícios prescritos com SVG animado e lembrete, adesão e dor, WhatsApp (Evolution, texto e MP4), equipe no Telegram, cadastros, gestão de agenda, backup e Docker.

VERIFICAÇÃO (só termina quando todos passarem, mostrando a saída):
- `python3 -m pytest -q tests/` → 98 passed, 0 failed, 0 errors
- `bash longrun/2026-10-05-fisio-v1/verificar-limites.sh` → LIMITES OK

RESTRIÇÕES: não altere tests/, pytest.ini, docs/, goal.md, hash-congelado.txt, congelar.sh, verificar-*, loop.env, prompt.md; não reescreva a seção "Como rodar no seu ambiente" do README.md. Só biblioteca padrão; nenhuma API, rede externa, chave, `npx`, `npm` ou `docker`; servidor só em 127.0.0.1; matar só o PID que subiu (nunca `pkill -f`). `tools/render-exercicios` é escrito conforme a seção 25 da spec, não executado. Uso só pela assinatura. Commit local a cada checkpoint com autor inematds; sem push, sem repo remoto.

ESTADO: use longrun/2026-10-05-fisio-v1/ (goal.md, plan.md, state.md, progress.md, failures.md, decisions.md, canal.md).
Após qualquer compactação ou retomada, releia goal.md, state.md, plan.md e canal.md antes de agir. Registre no canal.md (só acrescentar) fatos, aprendizados, glossário e armadilhas assim que surgirem.

CICLO: analisar → escolher a próxima ação útil → executar → testar → observar → corrigir → atualizar state/progress → commit no checkpoint → continuar.
Ordem sugerida: base (serve/PORTA/SQLite/auth) → agenda → conversa → confirmação/espera → planos e alertas → biblioteca, páginas e 12 SVGs → prescrição/lembrete/adesão/dor → campanhas → LGPD → raiox → cadastros/bloqueios/backup → Evolution → Telegram → Docker/README → /equipe → tools/render-exercicios.
O projeto irmão ~/projetos/atende-clinica tem a implementação do molde; reaproveite o que a spec deste repo mantém igual.
Evolution e Telegram: só pelas variáveis de ambiente, testados contra o servidor falso dos testes; nunca chamar API real. O bot nunca dá orientação clínica.
Enquanto existir uma próxima ação objetiva, segura e alinhada ao objetivo, execute-a sem esperar nova instrução.
3 ciclos sem avanço mensurável (nº de testes passando) = parar, registrar em failures.md e me chamar.
Teste que contradiz a especificação = registrar em failures.md e me chamar; nunca alterar teste ou spec.

PARE E ME CHAME SÓ SE: gasto de crédito/API, ação irreversível ou externa (push, repo remoto, apagar), dependência externa, credencial ausente, decisão de negócio, conflito real entre teste e especificação.
