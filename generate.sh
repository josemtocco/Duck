#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

echo "▶ Instalando dependências (se necessário)…"
python3 -m pip install -q -r requirements.txt

echo "▶ Gerando lista M3U…"
python3 -m src.generate_m3u

echo "▶ Pronto. Arquivo: TVplus.m3u"
