# Plano (reescrever, não acumular)

## Estratégia atual
Plano pronto (spec + 98 testes congeláveis + travas); implementação ainda não começou. O implementador parte do molde `~/projetos/atende-clinica` (mesma pilha) e acrescenta as seções 20–25 da spec. Ordem: base → agenda → conversa → confirmação/espera → planos/alertas → biblioteca + páginas + 12 SVGs → prescrição/lembrete/adesão/dor → campanhas → LGPD → raiox → cadastros/bloqueios/backup → Evolution → Telegram → Docker/README → /equipe → tools/render-exercicios (escrito, não executado).

## Próximos passos
1. Dono responde `docs/DECISOES-ABERTAS.md`, faz o commit e roda `longrun/2026-10-05-fisio-v1/congelar.sh`.
2. Inicia o loop headless (`~/projetos/execucao-longa/tools/loop-longrun.sh longrun/2026-10-05-fisio-v1`) ou cola o `/goal` (ver `prompt-goal-*.md`).
3. Depois do "concluído": `python3 longrun/2026-10-05-fisio-v1/verificar-independente.py`, abrir `/`, `/equipe` e `/exercicios/ponte`, revisar o conteúdo clínico dos 12 exercícios e rodar `tools/render-exercicios`.
