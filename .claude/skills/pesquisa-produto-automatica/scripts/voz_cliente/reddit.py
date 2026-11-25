#!/usr/bin/env python3
"""Coleta posts e comentários do Reddit no formato bruto comum, com backend plugável.

Backends (--backend):
  oauth   OAuth application-only (client_credentials) com REDDIT_CLIENT_ID e
          REDDIT_CLIENT_SECRET do .env da raiz do projeto. Busca posts por termo
          (opcionalmente em subreddits) e lê os comentários de cada post.
  arquivo Lê JSON/JSONL que outra etapa (ex.: navegador do Overclock) salvou em
          disco. Aceita (a) registros já no formato bruto, (b) objetos da API do
          Reddit (listing / "kind":"t1"|"t3" / "data"), ou (c) objetos simples com
          as chaves abaixo. Campos de autor são ignorados.
  auto    (padrão) usa todos os backends que tiverem insumo: oauth se houver
          credenciais, arquivo se houver arquivo. Nenhum com dados -> registra
          em nao_consegui e sai limpo (código 0).

Contrato do modo arquivo (um objeto por linha no .jsonl, ou lista no .json):
  {"tipo": "post"|"comentario", "texto": "...", "permalink": "https://www.reddit.com/r/.../comments/ID/.../CID/",
   "titulo": "título do post", "subreddit": "SkincareAddiction", "likes": 12,
   "data": "2025-03-01" | "created_utc": 1740787200, "termo": "termo usado na busca"}
  Sinônimos aceitos: body/selftext -> texto; score/ups -> likes; url -> permalink; title -> titulo.

Uso:
  python3 reddit.py --termos 'dark spots; age spots over 50' --subreddits 'SkincareAddiction;30PlusSkinCare' \
      --saida brutos/reddit.jsonl [--backend auto] [--arquivo pasta/ou/arquivo.jsonl]
"""
import argparse
import base64
import glob
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import comum  # noqa: E402

USER_AGENT = "script:voz-cliente-pesquisa:v1.0 (pesquisa de voz do cliente, uso interno; read-only)"
BASE = "https://oauth.reddit.com"
CAMPOS_AUTOR = ("author", "author_fullname", "autor", "user", "username", "handle")


# ---------------------------------------------------------------- OAuth
class RedditOAuth:
    def __init__(self, client_id, client_secret, pausa=1.1):
        self.cid, self.secret, self.pausa = client_id, client_secret, pausa
        self.token, self._ultimo = None, 0.0

    def autenticar(self):
        auth = base64.b64encode(("%s:%s" % (self.cid, self.secret)).encode()).decode()
        req = urllib.request.Request(
            "https://www.reddit.com/api/v1/access_token",
            data=urllib.parse.urlencode({"grant_type": "client_credentials"}).encode(),
            headers={"Authorization": "Basic " + auth, "User-Agent": USER_AGENT})
        with urllib.request.urlopen(req, timeout=30) as r:
            d = json.loads(r.read().decode())
        if "access_token" not in d:
            raise RuntimeError("token não veio: %s" % str(d)[:200])
        self.token = d["access_token"]

    def get(self, caminho, params):
        espera = self.pausa - (time.time() - self._ultimo)
        if espera > 0:
            time.sleep(espera)
        url = BASE + caminho + "?" + urllib.parse.urlencode(dict(params, raw_json=1))
        for tentativa in range(3):
            req = urllib.request.Request(url, headers={"Authorization": "bearer " + self.token,
                                                       "User-Agent": USER_AGENT})
            try:
                self._ultimo = time.time()
                with urllib.request.urlopen(req, timeout=30) as r:
                    return json.loads(r.read().decode())
            except urllib.error.HTTPError as e:
                if e.code == 429 and tentativa < 2:
                    time.sleep(int(e.headers.get("Retry-After") or 10))
                    continue
                if e.code == 401 and tentativa < 2:
                    self.autenticar()
                    continue
                raise
        return None


def _achatar_comentarios(filhos, out, profundidade=0, max_prof=2):
    for ch in filhos or []:
        if ch.get("kind") != "t1":
            continue
        d = ch.get("data") or {}
        out.append(d)
        rep = d.get("replies")
        if profundidade < max_prof and isinstance(rep, dict):
            _achatar_comentarios((rep.get("data") or {}).get("children"), out, profundidade + 1, max_prof)


def coletar_oauth(cli, termos, subreddits, posts_por_termo, comentarios_por_post, status):
    registros, vistos = [], set()
    alvos = ["/r/%s/search" % s for s in subreddits] if subreddits else ["/search"]
    for termo in termos:
        for alvo in alvos:
            params = {"q": termo, "limit": posts_por_termo, "sort": "relevance", "t": "all", "type": "link"}
            if alvo != "/search":
                params["restrict_sr"] = 1
            try:
                lst = cli.get(alvo, params) or {}
            except Exception as e:  # noqa: BLE001
                status["nao_consegui"].append("Reddit busca '%s' em %s: %s" % (termo, alvo, e))
                continue
            posts = [c.get("data") or {} for c in (lst.get("data") or {}).get("children", [])]
            comum.log("reddit: '%s' %s -> %d posts" % (termo, alvo, len(posts)))
            for p in posts:
                pid = p.get("id")
                if not pid or pid in vistos:
                    continue
                vistos.add(pid)
                url_post = "https://www.reddit.com" + (p.get("permalink") or "")
                base = {"fonte": "reddit", "termo": termo, "url": url_post, "post_id": pid,
                        "titulo": p.get("title"), "canal": "r/" + (p.get("subreddit") or "")}
                if (p.get("selftext") or "").strip() and p.get("selftext") not in ("[removed]", "[deleted]"):
                    registros.append(dict(base, tipo="post", texto=p["selftext"], likes=p.get("score") or 0,
                                          data=comum.ts_para_iso(p.get("created_utc")), permalink=url_post,
                                          id="rd:" + pid, e_resposta=False, do_autor_do_conteudo=False))
                try:
                    arv = cli.get("/comments/%s" % pid, {"limit": comentarios_por_post, "sort": "top",
                                                         "depth": 3}) or []
                except Exception as e:  # noqa: BLE001
                    status["nao_consegui"].append("Reddit comentários %s: %s" % (url_post, e))
                    continue
                coms = []
                if isinstance(arv, list) and len(arv) > 1:
                    _achatar_comentarios((arv[1].get("data") or {}).get("children"), coms)
                for c in coms[:comentarios_por_post]:
                    corpo = c.get("body")
                    if not corpo or corpo in ("[removed]", "[deleted]"):
                        continue
                    registros.append(dict(base, tipo="comentario", texto=corpo, likes=c.get("score") or 0,
                                          data=comum.ts_para_iso(c.get("created_utc")),
                                          permalink="https://www.reddit.com" + (c.get("permalink") or ""),
                                          id="rd:" + (c.get("id") or ""),
                                          e_resposta=not str(c.get("parent_id", "")).startswith("t3_"),
                                          do_autor_do_conteudo=bool(c.get("is_submitter"))))
    return registros


# ---------------------------------------------------------------- arquivo
def _itens_de(obj):
    """Desembrulha listing/kind/data e listas em objetos simples."""
    if isinstance(obj, list):
        for x in obj:
            for y in _itens_de(x):
                yield y
    elif isinstance(obj, dict):
        if obj.get("kind") == "Listing":
            for y in _itens_de((obj.get("data") or {}).get("children", [])):
                yield y
        elif obj.get("kind") in ("t1", "t3") and isinstance(obj.get("data"), dict):
            d = dict(obj["data"])
            d.setdefault("tipo", "comentario" if obj["kind"] == "t1" else "post")
            yield d
            rep = d.get("replies")
            if isinstance(rep, dict):
                for y in _itens_de(rep):
                    yield y
        else:
            yield obj


def _normalizar(d, origem):
    texto = d.get("texto") or d.get("body") or d.get("selftext") or d.get("text")
    if not texto or texto in ("[removed]", "[deleted]"):
        return None
    perma = d.get("permalink") or d.get("url") or ""
    if perma.startswith("/"):
        perma = "https://www.reddit.com" + perma
    tipo = d.get("tipo") or ("post" if d.get("selftext") or d.get("title") else "comentario")
    data = d.get("data") if isinstance(d.get("data"), str) else comum.ts_para_iso(d.get("created_utc"))
    sub = d.get("subreddit") or d.get("canal") or ""
    url_post = d.get("url_post") or (perma.split("/comments/")[0] + "/comments/" +
                                    perma.split("/comments/")[1].split("/")[0] + "/"
                                    if "/comments/" in perma else perma)
    rid = d.get("id") or d.get("name") or perma
    r = {"fonte": "reddit", "tipo": tipo, "termo": d.get("termo") or "arquivo", "url": url_post,
         "titulo": d.get("titulo") or d.get("title") or d.get("link_title"),
         "canal": sub if not sub or sub.startswith("r/") else "r/" + sub,
         "texto": texto, "likes": d.get("likes") if isinstance(d.get("likes"), int) else (d.get("score") or d.get("ups") or 0),
         "data": data, "permalink": perma, "id": rid if str(rid).startswith("rd:") else "rd:%s" % rid,
         "e_resposta": bool(d.get("e_resposta")), "do_autor_do_conteudo": bool(d.get("do_autor_do_conteudo")),
         "origem_arquivo": os.path.basename(origem)}
    for k in CAMPOS_AUTOR:
        r.pop(k, None)
    return r


def coletar_arquivo(caminhos, status):
    arquivos = []
    for c in caminhos:
        if os.path.isdir(c):
            arquivos += sorted(glob.glob(os.path.join(c, "*.json")) + glob.glob(os.path.join(c, "*.jsonl")))
        elif os.path.isfile(c):
            arquivos.append(c)
    registros = []
    for a in arquivos:
        try:
            if a.endswith(".jsonl"):
                objs = comum.ler_jsonl(a)
            else:
                with open(a, encoding="utf-8") as f:
                    objs = json.load(f)
        except Exception as e:  # noqa: BLE001
            status["nao_consegui"].append("Reddit arquivo %s ilegível: %s" % (a, e))
            continue
        n0 = len(registros)
        for d in _itens_de(objs):
            r = _normalizar(d, a)
            if r:
                registros.append(r)
        comum.log("reddit: arquivo %s -> %d registros" % (a, len(registros) - n0))
    status["arquivos_lidos"] = arquivos
    return registros


# ---------------------------------------------------------------- orquestração
def coletar(termos, subreddits=None, posts_por_termo=10, comentarios_por_post=50, backend="auto",
            arquivos=None, env=None, saida=None):
    t0 = time.time()
    status = {"fonte": "reddit", "inicio": comum.agora_iso(), "backend_pedido": backend,
              "backends_usados": [], "termos": termos, "subreddits": subreddits or [], "nao_consegui": []}
    registros = []
    arquivos_pedidos = [a for a in (arquivos or []) if a]
    arquivos = [a for a in arquivos_pedidos if os.path.exists(a)]

    if backend in ("auto", "oauth"):
        env_path = env or comum.achar_env()
        vals = comum.ler_env(env_path)
        cid, sec = vals.get("REDDIT_CLIENT_ID") or os.environ.get("REDDIT_CLIENT_ID"), \
            vals.get("REDDIT_CLIENT_SECRET") or os.environ.get("REDDIT_CLIENT_SECRET")
        if cid and sec:
            cli = RedditOAuth(cid, sec)
            try:
                cli.autenticar()
                registros += coletar_oauth(cli, termos, subreddits or [], posts_por_termo,
                                           comentarios_por_post, status)
                status["backends_usados"].append("oauth")
            except Exception as e:  # noqa: BLE001
                status["nao_consegui"].append("Reddit OAuth falhou na autenticação: %s" % e)
        elif backend == "oauth":
            status["nao_consegui"].append("Reddit OAuth: sem REDDIT_CLIENT_ID/REDDIT_CLIENT_SECRET (.env: %s)"
                                          % (env_path or "não encontrado"))

    if backend in ("auto", "arquivo"):
        if arquivos:
            registros += coletar_arquivo(arquivos, status)
            status["backends_usados"].append("arquivo")
        elif backend == "arquivo":
            status["nao_consegui"].append("Reddit arquivo: nenhum arquivo informado/existente")

    # dedup por id
    vistos, unicos = set(), []
    for r in registros:
        if r["id"] in vistos:
            continue
        vistos.add(r["id"])
        unicos.append(r)

    if not unicos:
        status["nao_consegui"].append(
            "Reddit: nenhum backend trouxe dados — sem credenciais OAuth válidas no .env e sem arquivo do "
            "navegador (%s). Acesso anônimo é bloqueado (403). Etapa seguiu sem Reddit."
            % (", ".join(arquivos_pedidos) or "nenhum caminho informado"))
    status["fim"] = comum.agora_iso()
    status["segundos"] = round(time.time() - t0, 1)
    status["n_comentarios"] = len(unicos)
    if saida:
        comum.salvar_jsonl(saida, unicos)
        comum.salvar_json(saida + ".status.json", status)
    return unicos, status


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--termos", action="append", default=[], help="termos separados por ; (pode repetir)")
    ap.add_argument("--subreddits", action="append", default=[], help="sem r/, separados por ;")
    ap.add_argument("--posts", type=int, default=10, help="posts por termo (oauth)")
    ap.add_argument("--comentarios", type=int, default=50, help="comentários por post (oauth)")
    ap.add_argument("--backend", choices=["auto", "oauth", "arquivo"], default="auto")
    ap.add_argument("--arquivo", action="append", default=[], help="arquivo .json/.jsonl ou pasta (modo arquivo)")
    ap.add_argument("--env", default=None, help="caminho do .env (padrão: procura subindo do cwd)")
    ap.add_argument("--saida", required=True)
    a = ap.parse_args()
    _, st = coletar(comum.dividir_termos(a.termos), comum.dividir_termos(a.subreddits), a.posts,
                    a.comentarios, a.backend, a.arquivo, a.env, a.saida)
    print(json.dumps({k: st[k] for k in ("backends_usados", "n_comentarios", "segundos", "nao_consegui")},
                     ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
