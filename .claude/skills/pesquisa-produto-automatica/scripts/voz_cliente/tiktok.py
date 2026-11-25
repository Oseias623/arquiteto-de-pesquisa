#!/usr/bin/env python3
"""Baixa comentários de vídeos do TikTok (sem login) para o formato bruto comum.

A BUSCA de vídeos não funciona por script (exige assinatura): os vídeos vêm do
navegador do Overclock (logado), que grava as URLs num arquivo. Este script só
lê os comentários, via `curl_cffi` impersonando o Chrome:
  GET https://www.tiktok.com/api/comment/list/?aid=1988&aweme_id=ID&count=50&cursor=N
A legenda (titulo) vem da própria página do vídeo (__UNIVERSAL_DATA_FOR_REHYDRATION__).

Arquivo de vídeos (videos.txt): uma URL ou ID por linha. Opcional:
  - "# termo: dark spots serum"  -> vale para as linhas seguintes
  - "URL<TAB>legenda"            -> usa essa legenda se a página não trouxer
  - linhas vazias e outros "#" são ignorados

Nunca gravamos nickname, unique_id ou uid de quem comentou. O handle do dono do
vídeo só é usado em memória para marcar do_autor_do_conteudo; a URL do vídeo
(permalink) é a fonte citável. Sem curl_cffi -> nao_consegui e sai com código 0.

Uso:
  python3 tiktok.py --videos brutos/tiktok_navegador/videos.txt --saida brutos/tiktok.jsonl \
      [--video URL_OU_ID ...] [--comentarios 150] [--pausa 1.0] [--termo 'dark spots']
"""
import argparse
import json
import os
import re
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import comum  # noqa: E402

API = "https://www.tiktok.com/api/comment/list/"
RX_URL = re.compile(r"tiktok\.com/@([\w.\-]+)/(?:video|photo)/(\d+)")
RX_ID = re.compile(r"^\d{15,22}$")
RX_DADOS = re.compile(r'<script id="__UNIVERSAL_DATA_FOR_REHYDRATION__"[^>]*>(.*?)</script>', re.S)
RX_MENCAO = re.compile(r"(?<![\w.])@[\w.\-]+")


def ler_videos(caminhos, extras=(), termo_padrao="tiktok"):
    """-> lista de dicts {id, dono, url, termo, legenda} sem repetição."""
    vistos, out = set(), []

    def _add(bruto, termo, legenda=None):
        bruto = bruto.strip()
        m = RX_URL.search(bruto)
        if m:
            dono, vid = m.group(1), m.group(2)
        elif RX_ID.match(bruto):
            dono, vid = None, bruto
        else:
            return False
        if vid in vistos:
            return True
        vistos.add(vid)
        url = "https://www.tiktok.com/@%s/video/%s" % (dono, vid) if dono else \
            "https://www.tiktok.com/video/%s" % vid
        out.append({"id": vid, "dono": dono, "url": url, "termo": termo, "legenda": legenda})
        return True

    for c in caminhos or []:
        if os.path.isdir(c):
            c = os.path.join(c, "videos.txt")
        if not os.path.isfile(c):
            continue
        termo = termo_padrao
        with open(c, encoding="utf-8") as f:
            for linha in f:
                linha = linha.rstrip("\n")
                s = linha.strip()
                if not s:
                    continue
                if s.startswith("#"):
                    m = re.match(r"#\s*termo\s*:\s*(.+)", s, re.I)
                    if m:
                        termo = m.group(1).strip()
                    continue
                partes = linha.split("\t", 1)
                _add(partes[0], termo, partes[1].strip() if len(partes) > 1 and partes[1].strip() else None)
    for e in extras or []:
        _add(e, termo_padrao)
    return out


def _legenda(sess, v):
    """Legenda e data do vídeo pela página; None se não der (não é fatal)."""
    try:
        it = {}
        for tentativa in range(2):  # a página às vezes vem sem os dados; 1 nova tentativa
            m = RX_DADOS.search(sess.get(v["url"], timeout=30).text)
            if m:
                d = json.loads(m.group(1)).get("__DEFAULT_SCOPE__", {}).get("webapp.video-detail", {})
                it = (d.get("itemInfo") or {}).get("itemStruct") or {}
            if it.get("desc") is not None or tentativa:
                break
            time.sleep(3)
        if not it:
            return None, None, None
        if not v["dono"]:
            v["dono"] = (it.get("author") or {}).get("uniqueId")
            if v["dono"]:
                v["url"] = "https://www.tiktok.com/@%s/video/%s" % (v["dono"], v["id"])
        n = (it.get("stats") or {}).get("commentCount")
        return it.get("desc") or None, comum.ts_para_iso(it.get("createTime")), n
    except Exception:  # noqa: BLE001
        return None, None, None


def _limpar_legenda(s):
    if not s:
        return None
    s = RX_MENCAO.sub("", s)  # sem handles, nem de marca
    return " ".join(s.split()) or None


def coletar_video(sess, v, max_com, pausa, status):
    legenda, data_video, n_total = _legenda(sess, v)
    titulo = _limpar_legenda(legenda or v.get("legenda"))
    regs, cursor, paginas = [], 0, 0
    while len(regs) < max_com:
        try:
            r = sess.get(API, params={"aid": "1988", "aweme_id": v["id"], "count": "50", "cursor": str(cursor)},
                         timeout=30)
            d = r.json()
        except Exception as e:  # noqa: BLE001
            status["nao_consegui"].append("TikTok comentários %s (cursor %s): %s" % (v["url"], cursor, e))
            break
        paginas += 1
        coms = d.get("comments") or []
        if d.get("status_code") not in (0, None) and not coms:
            status["nao_consegui"].append("TikTok %s: status_code=%s %s" % (
                v["url"], d.get("status_code"), d.get("status_msg") or ""))
            break
        for c in coms:
            texto = c.get("text") or ""
            if not texto.strip():
                continue
            u = c.get("user") or {}
            do_autor = bool(v["dono"]) and (u.get("unique_id") or "").lower() == v["dono"].lower()
            regs.append({
                "fonte": "tiktok", "tipo": "comentario", "termo": v["termo"], "url": v["url"],
                "video_id": v["id"], "titulo": titulo, "canal": None, "data_video": data_video,
                "texto": texto, "likes": int(c.get("digg_count") or 0), "data": comum.ts_para_iso(c.get("create_time")),
                "permalink": v["url"], "id": "tt:%s" % c.get("cid"), "idioma_api": c.get("comment_language"),
                "n_respostas": int(c.get("reply_comment_total") or 0), "e_resposta": False,
                "do_autor_do_conteudo": do_autor, "fixado": bool(c.get("stick_position")),
            })
            if len(regs) >= max_com:
                break
        if not d.get("has_more") or not coms:
            break
        cursor = d.get("cursor") or (cursor + len(coms))
        time.sleep(pausa)
    return regs, {"url": v["url"], "id": v["id"], "termo": v["termo"], "titulo": titulo,
                  "comentarios_no_video": n_total, "comentarios": len(regs), "paginas": paginas}


def coletar(caminhos=None, extras=None, max_com=150, pausa=1.0, termo_padrao="tiktok", saida=None):
    t0 = time.time()
    status = {"fonte": "tiktok", "inicio": comum.agora_iso(), "arquivos": [c for c in caminhos or []],
              "videos": [], "nao_consegui": []}
    registros = []
    videos = ler_videos(caminhos, extras, termo_padrao)
    if not videos:
        status["nao_consegui"].append("TikTok: nenhum vídeo informado (%s). A descoberta é pelo navegador "
                                      "(grave as URLs em brutos/tiktok_navegador/videos.txt)."
                                      % (", ".join(caminhos or []) or "sem arquivo"))
    else:
        try:
            from curl_cffi import requests as creq
        except ImportError:
            creq = None
            status["nao_consegui"].append("TikTok: curl_cffi não instalado (python3 -m pip install --user "
                                          "curl_cffi) — %d vídeos não coletados." % len(videos))
        if creq:
            sess = creq.Session(impersonate="chrome")
            for i, v in enumerate(videos, 1):
                regs, info = coletar_video(sess, v, max_com, pausa, status)
                comum.log("tiktok: [%d/%d] %s -> %d comentários" % (i, len(videos), v["url"], len(regs)))
                registros += regs
                status["videos"].append(info)
                time.sleep(pausa)
            vazios = [x["url"] for x in status["videos"] if not x["comentarios"]]
            if vazios and len(vazios) == len(videos):
                status["nao_consegui"].append("TikTok: nenhum vídeo devolveu comentários (bloqueio/IP?).")
    vistos, unicos = set(), []
    for r in registros:
        if r["id"] not in vistos:
            vistos.add(r["id"])
            unicos.append(r)
    status["fim"] = comum.agora_iso()
    status["segundos"] = round(time.time() - t0, 1)
    status["n_comentarios"] = len(unicos)
    if saida:
        comum.salvar_jsonl(saida, unicos)
        comum.salvar_json(saida + ".status.json", status)
    return unicos, status


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--videos", action="append", default=[], help="videos.txt (ou pasta que o contém); repetível")
    ap.add_argument("--video", action="append", default=[], help="URL ou ID avulso; repetível")
    ap.add_argument("--comentarios", type=int, default=150, help="máximo por vídeo")
    ap.add_argument("--pausa", type=float, default=1.0, help="segundos entre requisições")
    ap.add_argument("--termo", default="tiktok", help="termo para vídeos sem '# termo:'")
    ap.add_argument("--saida", required=True)
    a = ap.parse_args()
    _, st = coletar(a.videos, a.video, a.comentarios, a.pausa, a.termo, a.saida)
    print(json.dumps({"videos": len(st["videos"]), "n_comentarios": st["n_comentarios"], "segundos": st["segundos"],
                      "nao_consegui": st["nao_consegui"]}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
