#!/usr/bin/env python3
"""Grava comentários do Reddit lidos no navegador no JSONL do modo arquivo (contrato no topo de reddit.py).

O agente lê a página no navegador do Overclock, monta um LOTE (JSON) com o texto
VERBATIM de cada comentário e roda este script, que acrescenta ao JSONL sem repetir.

Lote = lista de objetos (ou listas na mesma ordem):
  {"subreddit": "30PlusSkinCare", "termo": "age spots", "titulo": "Sunspots?",
   "permalink": "/r/30PlusSkinCare/comments/1x56u2j/sunspots/pgk4ncj/", "likes": 372, "texto": "..."}
  ["30PlusSkinCare", "age spots", "Sunspots?", "/r/.../pgk4ncj/", 372, "..."]
- permalink do comentário (com o ID no fim) sempre que a página mostrar; senão o do tópico
  (o id vira tópico + hash do texto, e o registro é marcado).
- likes = votos mostrados ("1.7K" -> 1700); data opcional ("AAAA-MM-DD"), senão n/v.
- NUNCA inclua nome de autor. Comentário cortado pela leitura truncada: não grave pedaço.

Uso:
  python3 reddit_navegador.py <saida>/brutos/reddit_navegador/reddit_navegador.jsonl lote.json [lote2.json ...]
"""
import hashlib
import json
import os
import re
import sys

CHAVES = ("subreddit", "termo", "titulo", "permalink", "likes", "texto")
RX_CID = re.compile(r"/comments/(\w+)/[^/]*/(\w+)/?(?:\?.*)?$")
RX_POST = re.compile(r"/comments/(\w+)")


def _likes(v):
    if isinstance(v, (int, float)):
        return int(v)
    s = str(v or "0").strip().lower().replace(",", "")
    mult = 1000 if s.endswith("k") else 1
    try:
        return int(float(s.rstrip("k")) * mult)
    except ValueError:
        return 0


def anexar(saida, itens):
    vistos = set()
    if os.path.isfile(saida):
        with open(saida, encoding="utf-8") as f:
            for linha in f:
                if linha.strip():
                    d = json.loads(linha)
                    vistos.add(d.get("id") or d.get("permalink"))
    os.makedirs(os.path.dirname(os.path.abspath(saida)), exist_ok=True)
    n = 0
    with open(saida, "a", encoding="utf-8") as f:
        for it in itens:
            d = dict(zip(CHAVES, it)) if isinstance(it, list) else dict(it)
            texto, perma = d.get("texto") or "", d.get("permalink") or ""
            if not texto.strip() or "/comments/" not in perma:
                continue
            perma = re.sub(r"^https?://(?:old\.|www\.)?reddit\.com", "", perma)
            m = RX_CID.search(perma)
            rid = "rd:%s" % m.group(2) if m else "rd:%s:%s" % (
                RX_POST.search(perma).group(1), hashlib.sha1(texto.encode("utf-8")).hexdigest()[:10])
            if rid in vistos:
                continue
            vistos.add(rid)
            sub = (d.get("subreddit") or "").replace("r/", "")
            f.write(json.dumps({
                "id": rid, "tipo": "comentario", "texto": texto, "permalink": "https://www.reddit.com" + perma,
                "titulo": d.get("titulo"), "subreddit": sub, "likes": _likes(d.get("likes")),
                "data": d.get("data"), "termo": d.get("termo") or "navegador",
                "coletado_via": "navegador overclock" + ("" if m else " (link do tópico: comentário sem ID visível)"),
            }, ensure_ascii=False) + "\n")
            n += 1
    return n, len(vistos)


def main():
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    total_novos = 0
    for lote in sys.argv[2:]:
        with open(lote, encoding="utf-8") as f:
            itens = json.load(f)
        novos, total = anexar(sys.argv[1], itens)
        total_novos += novos
        print("%s: +%d (total no arquivo: %d)" % (os.path.basename(lote), novos, total))


if __name__ == "__main__":
    main()
