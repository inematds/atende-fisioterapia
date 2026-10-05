#!/usr/bin/env bash
# Camada "limite" do goal.md. Imprime LIMITES OK ou o primeiro problema (código ≠ 0).
set -uo pipefail
cd "$(git -C "$(dirname "$0")" rev-parse --show-toplevel)"
D=longrun/2026-10-05-fisio-v1
falha() { echo "LIMITE VIOLADO: $*"; exit 1; }
[ -f $D/hash-congelado.txt ] || falha "contrato não congelado (rode $D/congelar.sh)"
source $D/hash-congelado.txt
h=$(cat $(git ls-files tests pytest.ini docs/ESPECIFICACAO.md $D/verificar-limites.sh $D/verificar-independente.py | sort) | sha256sum | cut -c1-16)
[ "$h" = "$HASH" ] || falha "hash do contrato mudou ($h ≠ $HASH)"
git diff --quiet -- tests pytest.ini docs/ESPECIFICACAO.md $D/verificar-independente.py || falha "contrato alterado no working tree"
n=$(python3 -m pytest --collect-only -q 2>/dev/null | grep -oE '^[0-9]+ tests? collected' | grep -oE '^[0-9]+')
[ "$n" = "$TESTES" ] || falha "nº de testes coletados $n ≠ $TESTES"
fora=$( { git diff --name-only "$BASE"; git ls-files --others --exclude-standard; } | sort -u \
  | grep -vE "^($D/|atende$|src/|web/|tools/|exemplos/|README\.md$|VERSION$|Dockerfile$|docker-compose\.yml$|\.env\.exemplo$|\.dockerignore$|\.gitignore$|CLAUDE\.md$|FALHAS\.md$)" )
[ -z "$fora" ] || falha "arquivos fora do escopo: $(echo $fora)"
codigo=$(ls -d atende src web tools 2>/dev/null)
[ -n "$codigo" ] || falha "não há implementação (atende/src/web/tools)"
grep -q "Como rodar no seu ambiente" README.md || falha "README perdeu a seção do dono (Como rodar no seu ambiente)"
# credencial e host externo são barrados também nos arquivos de entrega (Dockerfile, compose, .env.exemplo, .dockerignore)
entrega=$(ls Dockerfile docker-compose.yml .env.exemplo .dockerignore 2>/dev/null)
grep -rnE '^\s*(import|from)\s+(requests|httpx|aiohttp|urllib3|flask|fastapi|django|openai|anthropic|groq|playwright|selenium)\b' $codigo && falha "dependência externa ou SDK de API"
grep -rnE '(OPENAI|ANTHROPIC|GROQ|OPENROUTER)_?API_KEY|sk-[A-Za-z0-9]{20,}|[0-9]{8,10}:[A-Za-z0-9_-]{30,}|graph\.facebook|api\.telegram\.org' $codigo $entrega && falha "chave/credencial ou API externa no código ou na entrega"
grep -rnP 'https?://(?!127\.0\.0\.1|localhost|www\.w3\.org)' $codigo $entrega && falha "URL externa no código ou na entrega"
grep -rn '0\.0\.0\.0' $codigo && falha "bind em 0.0.0.0 no código (só o comando do container pode passar --host)"
grep -rniE '<(script|animate|animateTransform|animateMotion|set)\b' web/exercicios/*.svg 2>/dev/null && falha "SVG com script ou SMIL (seção 21: só animação CSS)"
echo "LIMITES OK (hash $HASH, $TESTES testes, escopo ok, sem API/rede)"
