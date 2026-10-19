# Decisões (só acrescentar)

| data | decisão | motivo | alternativa descartada |
|---|---|---|---|
| 2026-10-19 13:50 | Reutilizar módulos do atende-clinica e banco SQLite sob RLock/transação por requisição; backlog HTTP 64 | base comum da spec e concorrência local | reescrever base inteira |
| 2026-10-19 13:54 | Contagens de plano calculadas da agenda; índice SQLite único para plano ativo; retorno criado na transição de conclusão | evitar contadores divergentes e duplicação de retornos | contadores incrementais separados |
| 2026-10-19 13:54 | Guardar última sessão realizada da sequência alertada além do timestamp exigido | presença pode ser futura em relação ao relógio; preservar idempotência por sequência | comparar somente timestamps e repetir alerta a cada rodada |
| 2026-10-19 13:58 | Biblioteca em módulo independente reutiliza catalogo SQLite e lock do servidor; HTML em template web com escape de conteúdo | preservar ordem/persistência e impedir conteúdo de cadastro virar marcação executável | HTML montado sem escape ou catálogo duplicado |
| 2026-10-19 13:58 | SVGs com movimentos próprios por transformação/CSS d, durações 2/4 s e pausa por movimento reduzido; MP4 só lido do diretório configurado | contrato de animação local, acessibilidade e build humano posterior | SMIL, scripts, render ou download no servidor |
| 2026-10-19 14:02 | Preferências de lembrete em pacientes; prescrições versionadas em tabela com índice único parcial para ativa; itens guardam nome da criação | substituição preserva opt-in/hora e histórico da prescrição | preferências copiadas a cada prescrição |
| 2026-10-19 14:02 | Registro diário único por paciente/data com atualização independente de fez/dor; agregados derivados da prescrição ativa | mensagens no mesmo dia não duplicam nem apagam campo omitido | contadores de adesão incrementais |
| 2026-10-19 14:02 | enviar/registrar aceitam instante opcional usado pelo lembrete; resposta do paciente usa relógio do processo | idempotência por data da rodada e histórico coerente; contrato distingue os dois relógios | datar lembrete com relógio fixo do processo |
| 2026-10-19 14:08 | Coluna migrada saida.exercicio_id; entrega e reenvio escolhem sendMedia pelo arquivo e PUBLIC_URL; respostas processadas são informadas ao webhook | preservar reenvio após reinício, evitar envio duplo e respeitar nao_contatar; histórico fica com conversar | inferir ID pelo texto ou enviar novamente no webhook |

| 2026-10-19 14:11 | Compose usa bind mounts dados/backups e web/exercicios somente leitura; Dockerfile cria /dados e usa healthcheck Python | persistência, backup por cron e MP4 copiados sem rebuild; sem dependências Python | dados efêmeros ou instalação de curl |
