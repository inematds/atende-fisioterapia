# Estado — atualizado 2026-10-05 (planejamento)

## Funciona
- Nada implementado ainda (sem `atende`, `src/`, `web/`, `tools/`). Contrato, fixture, 98 testes caixa-preta e travas prontos.
- `python3 -m pytest -q --collect-only` → 98 coletados; `python3 -m pytest -q` → 0 passed (todos falham por falta do `./atende`).

## Falta
- Tudo da spec (seções 1–25). Começar pela base (`./atende serve` com `PORTA=<n>`, SQLite, auth).

## Como retomar (comandos exatos)
```
cd ~/projetos/atende-fisioterapia
python3 -m pytest -q tests/ | tail -30
bash longrun/2026-10-05-fisio-v1/verificar-limites.sh
```

Ao retomar/após compactação: ler goal.md → state.md → plan.md → fim de progress.md e failures.md.
