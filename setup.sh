#!/usr/bin/env bash
set -e
cd "$(dirname "$0")"

if [ ! -f ".venv/bin/python" ]; then
  echo "Criando ambiente virtual em .venv ..."
  python3 -m venv .venv
else
  echo "Ambiente virtual ja existe, pulando criacao."
fi

echo "Instalando dependencias..."
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -r requirements.txt

echo
echo "Setup concluido! Use ./start.sh para iniciar o servidor."
