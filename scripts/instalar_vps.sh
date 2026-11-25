#!/bin/sh
# Instala as dependências da pesquisa numa VPS Ubuntu/Debian e registra a skill no Hermes Agent.
# Rode como usuário comum (não root), de dentro do repositório:  sh scripts/instalar_vps.sh
# Não pede nem grava nenhuma credencial: os logins são feitos depois, à mão (ver docs/VPS-HERMES.md).
set -e
[ "$(id -u)" -eq 0 ] && { echo "Rode como usuário comum (com sudo), não como root."; exit 1; }
REPO=$(cd "$(dirname "$0")/.." && pwd)

echo "== pacotes do sistema"
sudo apt-get update -qq
sudo apt-get install -y -qq python3 python3-pip python3-venv ffmpeg git cmake build-essential curl nodejs npm

echo "== Python: openpyxl, uv, yt-dlp com curl-cffi"
python3 -m pip install --user -q openpyxl 2>/dev/null || python3 -m pip install --user -q --break-system-packages openpyxl
command -v uv >/dev/null || curl -LsSf https://astral.sh/uv/install.sh | sh
export PATH="$HOME/.local/bin:$PATH"
uv tool install --force "yt-dlp[default,curl-cffi]"

echo "== whisper.cpp + modelo small"
if ! command -v whisper-cli >/dev/null; then
  [ -d ~/.local/src/whisper.cpp ] || git clone -q https://github.com/ggml-org/whisper.cpp ~/.local/src/whisper.cpp
  (cd ~/.local/src/whisper.cpp && cmake -B build -DCMAKE_BUILD_TYPE=Release >/dev/null && cmake --build build -j >/dev/null)
  mkdir -p ~/.local/bin && ln -sf ~/.local/src/whisper.cpp/build/bin/whisper-cli ~/.local/bin/whisper-cli
fi
mkdir -p ~/.cache/whisper-cpp
[ -f ~/.cache/whisper-cpp/ggml-small.bin ] || (cd ~/.local/src/whisper.cpp && sh ./models/download-ggml-model.sh small >/dev/null && mv models/ggml-small.bin ~/.cache/whisper-cpp/)

echo "== navegador headless (Playwright Chromium)"
npx -y playwright install --with-deps chromium >/dev/null

echo "== skill no Hermes Agent (link: um git pull atualiza)"
mkdir -p ~/.hermes/skills/research
ln -sfn "$REPO/.claude/skills/pesquisa-produto-automatica" ~/.hermes/skills/research/pesquisa-produto-automatica

echo "== proteções"
git -C "$REPO" config core.hooksPath .githooks
[ -f "$REPO/.env" ] && chmod 600 "$REPO/.env"
echo "Pronto. Agora: sh scripts/verificar_ambiente.sh e siga docs/VPS-HERMES.md (logins)."
