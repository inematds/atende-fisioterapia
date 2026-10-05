# FALHAS

| data | o que quebrou | menor correção | prompt \| infra |
|---|---|---|---|
| 2026-10-05 | validação do plano: §17 mandava a explicação de exercício para a caixa de saída sem `tipo` próprio; o único próximo (`exercicio`) é a pendência da regra 6 — implementador honesto passaria em `test_exercicio_com_mp4_vai_por_sendmedia` e faria "7" depois de "como faço a ponte?" virar dor 7 + fila alta | `tipo: "explicacao"` no enum da §5, na regra 9 e na §17; regra 6 enumera as 3 pendências que contam | prompt |
| 2026-10-05 | validação do plano: cabeçalho da §6 trocava pontuação por espaço, então `lembrete 20:30` virava `lembrete 20 30` e `test_lembrete_opt_in_pelo_chat` cobra `"20:30"` | regra 7: hora lida do texto original por `\d{1,2}:\d{2}` | prompt |
