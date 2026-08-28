#!/usr/bin/env bash
set -e
cd "$(dirname "$0")"

if [ ! -f ".venv/bin/python" ]; then
  echo "Ambiente virtual nao encontrado. Rode ./setup.sh primeiro."
  exit 1
fi

PORT=8010
echo "Iniciando servidor em http://localhost:${PORT}"
echo "(pressione CTRL+C para parar)"

( sleep 2; xdg-open "http://localhost:${PORT}" 2>/dev/null || open "http://localhost:${PORT}" 2>/dev/null || true ) &

.venv/bin/python -m uvicorn app.main:app --reload --port "${PORT}"
