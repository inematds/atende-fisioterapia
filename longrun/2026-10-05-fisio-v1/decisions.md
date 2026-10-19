# Decisões (só acrescentar)

| data | decisão | motivo | alternativa descartada |
|---|---|---|---|
| 2026-10-19 13:50 | Reutilizar módulos do atende-clinica e banco SQLite sob RLock/transação por requisição; backlog HTTP 64 | base comum da spec e concorrência local | reescrever base inteira |
| 2026-10-19 13:54 | Contagens de plano calculadas da agenda; índice SQLite único para plano ativo; retorno criado na transição de conclusão | evitar contadores divergentes e duplicação de retornos | contadores incrementais separados |
| 2026-10-19 13:54 | Guardar última sessão realizada da sequência alertada além do timestamp exigido | presença pode ser futura em relação ao relógio; preservar idempotência por sequência | comparar somente timestamps e repetir alerta a cada rodada |
