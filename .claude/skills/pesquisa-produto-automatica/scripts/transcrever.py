#!/usr/bin/env python3
"""Transcreve um vídeo de anúncio por áudio (whisper.cpp) e, opcional, gera mosaico de frames.

Uso:
  python3 transcrever.py VIDEO [--frames 16] [--modelo small] [--idioma auto] [--preciso] [--pasta DIR] [--saida x.json]

VIDEO = arquivo local, link da Biblioteca da Meta (…/ads/library/?id=ID) ou qualquer URL que o yt-dlp baixe.

Saída (stdout e --saida): JSON
  {fonte, arquivo, idioma, duracao, tempo_gasto, modelo, fala_verificada,
   segmentos: [{inicio, fim, texto}], texto, mosaicos: [...], nao_consegui: [...]}

- Meta: o yt-dlp toma 403 (desafio JS "rd_challenge"). O script resolve sozinho com curl_cffi:
  GET → POST no /__rd_verify_… → GET de novo → lê video_hd_url/video_sd_url → baixa o mp4.
  curl_cffi vem no Python do yt-dlp (uv); se o python3 atual não tiver, o script se reexecuta nele.
- Sem whisper-cli ou sem modelo: não falha; devolve fala_verificada=false, "fala não verificada".
- Mosaico (--frames N): 1 frame/s, N frames por folha (grade quadrada), largura 320 px por célula.
  Célula k da folha f (contando da esquerda p/ direita, de cima p/ baixo, a partir de 0) = segundo f*N + k.
"""
import argparse
import glob
import json
import math
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time

HOME = os.path.expanduser("~")
MODELOS_DIR = os.environ.get("WHISPER_MODELS_DIR", os.path.join(HOME, ".cache", "whisper-cpp"))
YTDLP_PY = os.path.join(HOME, ".local", "share", "uv", "tools", "yt-dlp", "bin", "python")
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0 Safari/537.36"


def achar_bin(nome, extras=()):
    p = shutil.which(nome)
    if p:
        return p
    for c in extras:
        if os.path.isfile(c) and os.access(c, os.X_OK):
            return c
    return None


def whisper_bin():
    return achar_bin("whisper-cli", [
        os.path.join(HOME, ".local", "bin", "whisper-cli"),
        os.path.join(HOME, ".local", "src", "whisper.cpp", "build", "bin", "whisper-cli"),
        "/usr/local/bin/whisper-cli", "/opt/homebrew/bin/whisper-cli",
    ])


def ytdlp_bin():
    return achar_bin("yt-dlp", [os.path.join(HOME, ".local", "bin", "yt-dlp")])


def modelo_path(m):
    if os.path.isfile(m):
        return m
    p = os.path.join(MODELOS_DIR, "ggml-%s.bin" % m)
    return p if os.path.isfile(p) else None


def eh_meta(url):
    return "facebook.com/ads/library" in url and re.search(r"[?&]id=\d+", url)


def baixar_meta(url, pasta):
    """Baixa o vídeo de um anúncio da Biblioteca da Meta sem navegador (curl_cffi + desafio rd_challenge)."""
    from curl_cffi import requests  # import aqui: só a Meta precisa
    ad_id = re.search(r"[?&]id=(\d+)", url).group(1)
    s = requests.Session(impersonate="chrome")
    pag = "https://www.facebook.com/ads/library/?id=" + ad_id
    r = s.get(pag, timeout=30)
    m = re.search(r"fetch\('(/__rd_verify[^']+)'", r.text)
    if m:
        s.post("https://www.facebook.com" + m.group(1), timeout=30,
               headers={"Origin": "https://www.facebook.com", "Referer": pag})
        time.sleep(1)
        r = s.get(pag, timeout=30)
    if r.status_code != 200:
        raise RuntimeError("Biblioteca da Meta respondeu HTTP %s para o anúncio %s" % (r.status_code, ad_id))
    t = r.text
    urls = [u.replace("\\/", "/") for u in re.findall(r'"video_hd_url":"([^"]+)"', t)]
    urls += [u.replace("\\/", "/") for u in re.findall(r'"video_sd_url":"([^"]+)"', t)]
    if not urls:
        raise RuntimeError("anúncio %s sem video_hd_url/video_sd_url (imagem/carrossel ou página mudou)" % ad_id)
    destino = os.path.join(pasta, "meta_%s.mp4" % ad_id)
    v = s.get(urls[0], timeout=120)
    if v.status_code != 200 or len(v.content) < 10000:
        raise RuntimeError("download do mp4 falhou (HTTP %s)" % v.status_code)
    with open(destino, "wb") as f:
        f.write(v.content)
    return destino


def baixar_ytdlp(url, pasta):
    yt = ytdlp_bin()
    if not yt:
        raise RuntimeError("yt-dlp não encontrado")
    modelo = os.path.join(pasta, "video_%(id)s.%(ext)s")
    cmd = [yt, "--impersonate", "chrome", "--no-playlist", "-q", "--no-warnings",
           "-f", "bv*[height<=720]+ba/b[height<=720]/b", "--merge-output-format", "mp4", "-o", modelo, url]
    p = subprocess.run(cmd, capture_output=True, text=True)
    if p.returncode != 0:
        raise RuntimeError("yt-dlp: " + (p.stderr.strip().splitlines() or ["erro"])[-1])
    arqs = sorted(glob.glob(os.path.join(pasta, "video_*")), key=os.path.getmtime)
    if not arqs:
        raise RuntimeError("yt-dlp não gerou arquivo")
    return arqs[-1]


def duracao(arq):
    p = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                        "-of", "default=nw=1:nk=1", arq], capture_output=True, text=True)
    try:
        return round(float(p.stdout.strip()), 2)
    except ValueError:
        return None


def extrair_audio(arq, wav):
    p = subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", arq, "-vn", "-ac", "1", "-ar", "16000",
                        "-c:a", "pcm_s16le", wav], capture_output=True, text=True)
    if p.returncode != 0 or not os.path.isfile(wav):
        raise RuntimeError("ffmpeg (áudio): " + p.stderr.strip()[-300:])


def nucleos_fisicos():
    # Hyper-threading atrapalha o whisper: no i5-8210Y, 2 threads (núcleos reais) = 73 s/min; 4 threads = 98 s/min.
    try:
        return int(subprocess.run(["sysctl", "-n", "hw.physicalcpu"], capture_output=True, text=True).stdout)
    except ValueError:
        return max(1, (os.cpu_count() or 2) // 2)


def transcrever(wav, modelo, idioma, base, preciso=False):
    cli = whisper_bin()
    busca = ["-bs", "5", "-bo", "5"] if preciso else ["-bs", "1", "-bo", "1"]  # gulosa: ~2,8x mais rápida
    cmd = [cli, "-m", modelo, "-f", wav, "-l", idioma, "-oj", "-of", base,
           "-t", str(nucleos_fisicos()), "-np"] + busca
    p = subprocess.run(cmd, capture_output=True, text=True)
    if p.returncode != 0 or not os.path.isfile(base + ".json"):
        raise RuntimeError("whisper-cli: " + (p.stderr.strip()[-300:] or "sem saída"))
    with open(base + ".json", encoding="utf-8", errors="replace") as f:
        d = json.load(f)
    segs = []
    for s in d.get("transcription", []):
        txt = s.get("text", "").strip()
        if not txt:
            continue
        o = s.get("offsets", {})
        segs.append({"inicio": round(o.get("from", 0) / 1000, 2), "fim": round(o.get("to", 0) / 1000, 2), "texto": txt})
    lang = (d.get("result") or {}).get("language")
    return segs, lang


def mosaicos(arq, n, pasta, nome):
    lado = max(1, math.ceil(math.sqrt(n)))
    linhas = max(1, math.ceil(n / lado))
    saida = os.path.join(pasta, nome + "_mosaico_%02d.jpg")
    for antigo in glob.glob(os.path.join(pasta, nome + "_mosaico_*.jpg")):
        os.remove(antigo)
    vf = "fps=1,scale=320:-2,tile=%dx%d:padding=4:margin=4" % (lado, linhas)
    p = subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", arq, "-vf", vf, "-q:v", "3", saida],
                       capture_output=True, text=True)
    if p.returncode != 0:
        raise RuntimeError("ffmpeg (mosaico): " + p.stderr.strip()[-300:])
    return sorted(glob.glob(os.path.join(pasta, nome + "_mosaico_*.jpg")))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("video")
    ap.add_argument("--frames", type=int, default=0, help="frames por folha de mosaico (1 fps); 0 = sem mosaico")
    ap.add_argument("--modelo", default=os.environ.get("WHISPER_MODEL", "small"),
                    help="small (padrão), base, ou caminho de um ggml-*.bin")
    ap.add_argument("--idioma", default="auto", help="auto (padrão), en, pt…")
    ap.add_argument("--preciso", action="store_true", help="beam search 5 (≈2,8x mais lento; só p/ fala difícil)")
    ap.add_argument("--pasta", help="onde guardar vídeo/áudio/mosaicos (padrão: pasta temporária)")
    ap.add_argument("--saida", help="grava o JSON também neste arquivo")
    a = ap.parse_args()

    t0 = time.time()
    pasta = os.path.abspath(a.pasta) if a.pasta else tempfile.mkdtemp(prefix="transcrever_")
    os.makedirs(pasta, exist_ok=True)
    out = {"fonte": a.video, "arquivo": None, "idioma": None, "duracao": None, "tempo_gasto": None,
           "modelo": None, "fala_verificada": False, "segmentos": [], "texto": "", "mosaicos": [],
           "nao_consegui": []}

    def fim(code=0):
        out["tempo_gasto"] = round(time.time() - t0, 1)
        j = json.dumps(out, ensure_ascii=False, indent=2)
        if a.saida:
            with open(a.saida, "w", encoding="utf-8") as f:
                f.write(j + "\n")
        print(j)
        sys.exit(code)

    if not shutil.which("ffmpeg"):
        out["nao_consegui"].append("ffmpeg não instalado: sem áudio nem frames")
        out["texto"] = "fala não verificada"
        fim(0)

    # 1. obter o arquivo
    arq = a.video
    if re.match(r"https?://", a.video):
        try:
            arq = baixar_meta(a.video, pasta) if eh_meta(a.video) else baixar_ytdlp(a.video, pasta)
        except Exception as e:  # noqa: BLE001 — registrar e sair limpo
            out["nao_consegui"].append("download: %s" % e)
            out["texto"] = "fala não verificada"
            fim(0)
    elif not os.path.isfile(arq):
        out["nao_consegui"].append("arquivo não existe: %s" % arq)
        out["texto"] = "fala não verificada"
        fim(0)
    out["arquivo"] = os.path.abspath(arq)
    out["duracao"] = duracao(arq)
    nome = os.path.splitext(os.path.basename(arq))[0]

    # 2. mosaico (independe do whisper)
    if a.frames > 0:
        try:
            out["mosaicos"] = mosaicos(arq, a.frames, pasta, nome)
            out["mosaico_info"] = "1 fps; %d frames por folha; célula k da folha f = segundo f*%d+k" % (a.frames, a.frames)
        except Exception as e:  # noqa: BLE001
            out["nao_consegui"].append(str(e))

    # 3. fala
    modelo = modelo_path(a.modelo)
    if not whisper_bin() or not modelo:
        falta = "whisper-cli" if not whisper_bin() else "modelo %s em %s" % (a.modelo, MODELOS_DIR)
        out["nao_consegui"].append("%s não encontrado: fala não verificada" % falta)
        out["texto"] = "fala não verificada"
        fim(0)
    out["modelo"] = os.path.basename(modelo)
    wav = os.path.join(pasta, nome + "_16k.wav")
    try:
        extrair_audio(arq, wav)
        segs, lang = transcrever(wav, modelo, a.idioma, os.path.join(pasta, nome + "_whisper"), a.preciso)
    except Exception as e:  # noqa: BLE001
        out["nao_consegui"].append(str(e) + " — fala não verificada")
        out["texto"] = "fala não verificada"
        fim(0)
    out["segmentos"] = segs
    out["idioma"] = lang
    out["fala_verificada"] = True
    out["texto"] = " ".join(s["texto"] for s in segs) or "(sem fala detectada)"
    fim(0)


if __name__ == "__main__":
    # A Meta exige curl_cffi; se este Python não tiver, reexecuta no Python do yt-dlp (uv), que tem.
    if any(eh_meta(x) for x in sys.argv[1:]) and os.environ.get("_TRANSCREVER_REEXEC") != "1":
        try:
            import curl_cffi  # noqa: F401
        except ImportError:
            if os.path.isfile(YTDLP_PY):
                os.environ["_TRANSCREVER_REEXEC"] = "1"
                os.execv(YTDLP_PY, [YTDLP_PY, "-I", os.path.abspath(__file__)] + sys.argv[1:])
    main()
