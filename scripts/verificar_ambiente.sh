#!/bin/sh
# Confere se a máquina tem tudo que a pesquisa usa. Não instala nada nem lê credenciais:
# só diz o que está faltando e o comando para resolver.
ok()  { printf '  [ok]    %s\n' "$1"; }
nao() { printf '  [falta] %s\n          → %s\n' "$1" "$2"; }

echo "Ferramentas"
command -v python3 >/dev/null && ok "python3 ($(python3 --version 2>&1))" || nao python3 "instale o Python 3.9+"
python3 -c 'import openpyxl' 2>/dev/null && ok openpyxl || nao openpyxl "python3 -m pip install --user openpyxl"
command -v yt-dlp >/dev/null && ok "yt-dlp" || nao yt-dlp 'uv tool install "yt-dlp[default,curl-cffi]"   (ou: pipx install "yt-dlp[default,curl-cffi]")'
yp=$(dirname "$(readlink -f "$(command -v yt-dlp 2>/dev/null)" 2>/dev/null)" 2>/dev/null)/python
if [ -x "$yp" ] && "$yp" -c 'import curl_cffi' 2>/dev/null; then ok "curl_cffi (no Python do yt-dlp)"
elif python3 -c 'import curl_cffi' 2>/dev/null; then ok "curl_cffi"
else nao curl_cffi 'reinstale o yt-dlp com o extra curl-cffi (comando acima) — usado no TikTok e nos vídeos da Meta'; fi
command -v ffmpeg >/dev/null && ok ffmpeg || nao ffmpeg "brew install ffmpeg"
command -v whisper-cli >/dev/null && ok whisper-cli || nao "whisper-cli (opcional, transcrição)" "ver README › Transcrição"
ls ~/.cache/whisper-cpp/ggml-small.bin >/dev/null 2>&1 && ok "modelo whisper small" || nao "modelo ~/.cache/whisper-cpp/ggml-small.bin (opcional)" "ver README › Transcrição"
command -v gcloud >/dev/null && ok gcloud || nao "gcloud (opcional, subir no Drive)" "brew install --cask google-cloud-sdk"

echo "Logins"
if command -v gcloud >/dev/null; then
  conta=$(gcloud config get-value account 2>/dev/null)
  if gcloud auth print-access-token >/dev/null 2>&1; then ok "gcloud logado (${conta:-?})"
  else nao "gcloud sem login" "gcloud auth login --enable-gdrive-access --no-launch-browser"; fi
fi
echo "  [manual] navegador logado em Facebook, Reddit e TikTok (ver README › Passo 3)"
[ -f .env ] && echo "  [info]  .env presente (não vai para o Git)" || true
