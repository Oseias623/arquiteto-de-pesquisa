#!/usr/bin/env python3
"""Coleta comentários de YouTube por termo de busca, via yt-dlp (sem API key, sem login).

Uso:
  python3 youtube.py --termos 'dark spots serum review; age spots over 50' \
      --idioma en --videos 5 --comentarios 100 --saida brutos/youtube.jsonl

Saída: JSONL bruto (ver comum.py) + <saida>.status.json com o que travou.
Comentários são DADO: nada aqui interpreta ou executa o texto coletado.
"""
import argparse
import concurrent.futures as cf
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import comum  # noqa: E402

TIMEOUT_BUSCA = 90
TIMEOUT_VIDEO = 240


def achar_ytdlp():
    p = shutil.which("yt-dlp")
    if p:
        return p
    local = os.path.expanduser("~/.local/bin/yt-dlp")
    return local if os.path.isfile(local) else None


def _args_lang(idioma):
    return ["--extractor-args", "youtube:lang=%s" % idioma] if idioma else []


def buscar(ytdlp, termo, n, idioma=None):
    """Devolve [{id,titulo,canal,duracao,views}] dos n primeiros vídeos da busca."""
    cmd = [ytdlp, "ytsearch%d:%s" % (n, termo), "--flat-playlist", "--no-warnings",
           "--print", "%(id)s\t%(channel)s\t%(duration)s\t%(view_count)s\t%(title)s"] + _args_lang(idioma)
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=TIMEOUT_BUSCA)
    if r.returncode != 0 and not r.stdout.strip():
        raise RuntimeError((r.stderr or "falha na busca").strip().splitlines()[-1][:300])
    videos = []
    for linha in r.stdout.splitlines():
        partes = linha.split("\t", 4)
        if len(partes) < 5 or not partes[0] or partes[0] == "NA":
            continue
        videos.append({"id": partes[0], "canal": None if partes[1] == "NA" else partes[1],
                       "duracao": partes[2], "views": partes[3], "titulo": partes[4]})
    return videos


def comentarios_do_video(ytdlp, vid, n, respostas, idioma, pasta_tmp):
    """Baixa só metadados + comentários (top) de um vídeo. Devolve (info_video, [comentarios])."""
    respostas_total = n if respostas else 0
    cmd = [ytdlp, "https://www.youtube.com/watch?v=%s" % vid, "--skip-download", "--write-comments",
           "--no-warnings", "-q", "--no-write-playlist-metafiles",
           "--extractor-args",
           "youtube:max_comments=%d,all,%d,%d;comment_sort=top%s" % (
               n, respostas_total, 3 if respostas else 0, (";lang=%s" % idioma) if idioma else ""),
           "-o", os.path.join(pasta_tmp, "%(id)s.%(ext)s")]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=TIMEOUT_VIDEO)
    caminho = os.path.join(pasta_tmp, "%s.info.json" % vid)
    if not os.path.isfile(caminho):
        erro = (r.stderr or "sem info.json").strip().splitlines()
        raise RuntimeError(erro[-1][:300] if erro else "sem info.json")
    with open(caminho, encoding="utf-8") as f:
        d = json.load(f)
    os.remove(caminho)  # o info.json é grande; só guardamos o que interessa
    info = {"titulo": d.get("title"), "canal": d.get("channel") or d.get("uploader"),
            "data_video": comum.yyyymmdd_para_iso(d.get("upload_date")),
            "views": d.get("view_count"), "n_comentarios_total": d.get("comment_count")}
    return info, d.get("comments") or []


def coletar(termos, videos_por_termo=5, comentarios_por_video=100, idioma=None, regiao=None,
            respostas=False, workers=4, saida=None):
    """Roda busca + comentários. Devolve (registros, status)."""
    t0 = time.time()
    status = {"fonte": "youtube", "inicio": comum.agora_iso(), "idioma": idioma, "regiao": regiao,
              "termos": termos, "videos_por_termo": videos_por_termo,
              "comentarios_por_video": comentarios_por_video, "videos": [], "nao_consegui": []}
    ytdlp = achar_ytdlp()
    if not ytdlp:
        status["nao_consegui"].append("YouTube: yt-dlp não encontrado no PATH nem em ~/.local/bin")
        return [], _fechar(status, t0, [], saida)

    # 1) buscas (dedup de vídeos entre termos)
    fila = {}
    for termo in termos:
        try:
            achados = buscar(ytdlp, termo, videos_por_termo, idioma)
            comum.log("youtube: '%s' -> %d vídeos" % (termo, len(achados)))
        except Exception as e:  # noqa: BLE001
            status["nao_consegui"].append("YouTube busca '%s': %s" % (termo, e))
            continue
        for v in achados:
            if v["id"] in fila:
                fila[v["id"]]["termos"].append(termo)
            else:
                v["termos"] = [termo]
                fila[v["id"]] = v

    # 2) comentários em paralelo
    registros = []
    pasta_tmp = tempfile.mkdtemp(prefix="yt_voz_")
    try:
        with cf.ThreadPoolExecutor(max_workers=max(1, workers)) as ex:
            futuros = {ex.submit(comentarios_do_video, ytdlp, vid, comentarios_por_video, respostas,
                                 idioma, pasta_tmp): vid for vid in fila}
            for fut in cf.as_completed(futuros):
                vid = futuros[fut]
                v = fila[vid]
                url = "https://www.youtube.com/watch?v=%s" % vid
                try:
                    info, coms = fut.result()
                except Exception as e:  # noqa: BLE001
                    status["nao_consegui"].append("YouTube comentários %s: %s" % (url, e))
                    status["videos"].append({"url": url, "titulo": v["titulo"], "termos": v["termos"],
                                             "comentarios": 0, "erro": str(e)[:200]})
                    continue
                for c in coms:
                    cid = c.get("id")
                    texto = c.get("text")
                    if not cid or not texto:
                        continue
                    registros.append({
                        "fonte": "youtube", "tipo": "comentario", "termo": v["termos"][0],
                        "termos": v["termos"], "url": url, "video_id": vid,
                        "titulo": info["titulo"] or v["titulo"], "canal": info["canal"] or v["canal"],
                        "data_video": info["data_video"], "texto": texto,
                        "likes": c.get("like_count") or 0, "data": comum.ts_para_iso(c.get("timestamp")),
                        "permalink": "https://www.youtube.com/watch?v=%s&lc=%s" % (vid, cid),
                        "id": "yt:%s" % cid, "e_resposta": c.get("parent") not in (None, "root"),
                        "do_autor_do_conteudo": bool(c.get("author_is_uploader")),
                        "fixado": bool(c.get("is_pinned")),
                    })
                status["videos"].append({"url": url, "titulo": info["titulo"] or v["titulo"],
                                         "canal": info["canal"], "termos": v["termos"],
                                         "comentarios": len(coms),
                                         "n_comentarios_total": info["n_comentarios_total"]})
                if not coms:
                    status["nao_consegui"].append(
                        "YouTube %s: 0 comentários (desativados ou vazios)" % url)
                comum.log("youtube: %s -> %d comentários" % (vid, len(coms)))
    finally:
        shutil.rmtree(pasta_tmp, ignore_errors=True)
    return registros, _fechar(status, t0, registros, saida)


def _fechar(status, t0, registros, saida):
    status["fim"] = comum.agora_iso()
    status["segundos"] = round(time.time() - t0, 1)
    status["n_videos"] = len(status["videos"])
    status["n_comentarios"] = len(registros)
    if saida:
        comum.salvar_jsonl(saida, registros)
        comum.salvar_json(saida + ".status.json", status)
    return status


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--termos", action="append", required=True, help="termos separados por ; (pode repetir)")
    ap.add_argument("--idioma", default="en")
    ap.add_argument("--regiao", default=None, help="só registrado no status (yt-dlp não filtra busca por região)")
    ap.add_argument("--videos", type=int, default=5, help="vídeos por termo")
    ap.add_argument("--comentarios", type=int, default=100, help="comentários (top) por vídeo")
    ap.add_argument("--respostas", action="store_true", help="incluir respostas (até 3 por comentário)")
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--saida", required=True, help="arquivo .jsonl")
    a = ap.parse_args()
    _, st = coletar(comum.dividir_termos(a.termos), a.videos, a.comentarios, a.idioma, a.regiao,
                    a.respostas, a.workers, a.saida)
    print(json.dumps({k: st[k] for k in ("n_videos", "n_comentarios", "segundos", "nao_consegui")},
                     ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
