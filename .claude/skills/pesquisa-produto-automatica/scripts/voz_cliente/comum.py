"""Funções compartilhadas da coleta de voz do cliente (só stdlib, Python 3.9+).

Formato BRUTO (uma linha JSONL por comentário/post):
  fonte, tipo, termo, url, titulo, canal, texto, likes, data, permalink, id,
  video_id/post_id, e_resposta, do_autor_do_conteudo
Nunca guardamos nome, handle ou id de autor.
"""
import datetime as _dt
import json
import os
import re
import sys


def agora_iso():
    return _dt.datetime.now().astimezone().isoformat(timespec="seconds")


def ts_para_iso(ts):
    """Unix timestamp -> data ISO (UTC, só a data). None se não houver."""
    if ts in (None, ""):
        return None
    try:
        return _dt.datetime.utcfromtimestamp(float(ts)).strftime("%Y-%m-%d")
    except (ValueError, OverflowError, OSError):
        return None


def yyyymmdd_para_iso(s):
    if not s or len(str(s)) != 8:
        return None
    s = str(s)
    return "%s-%s-%s" % (s[:4], s[4:6], s[6:])


def dividir_termos(valores):
    """Aceita lista de strings; cada uma pode ter vários termos separados por ; | ou quebra de linha."""
    termos = []
    for v in valores or []:
        for t in re.split(r"[;|\n]", v):
            t = t.strip()
            if t and t not in termos:
                termos.append(t)
    return termos


def salvar_jsonl(caminho, registros):
    os.makedirs(os.path.dirname(os.path.abspath(caminho)), exist_ok=True)
    with open(caminho, "w", encoding="utf-8") as f:
        for r in registros:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


def ler_jsonl(caminho):
    out = []
    with open(caminho, encoding="utf-8") as f:
        for linha in f:
            linha = linha.strip()
            if linha:
                try:
                    out.append(json.loads(linha))
                except ValueError:
                    pass
    return out


def salvar_json(caminho, obj):
    os.makedirs(os.path.dirname(os.path.abspath(caminho)), exist_ok=True)
    with open(caminho, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)


def achar_env(inicio=None):
    """Procura um .env subindo a partir de `inicio` (padrão: cwd) e da pasta do script."""
    candidatos = []
    for base in (inicio or os.getcwd(), os.path.dirname(os.path.abspath(__file__))):
        d = os.path.abspath(base)
        while True:
            candidatos.append(os.path.join(d, ".env"))
            pai = os.path.dirname(d)
            if pai == d:
                break
            d = pai
    for c in candidatos:
        if os.path.isfile(c):
            return c
    return None


def ler_env(caminho):
    vals = {}
    if not caminho or not os.path.isfile(caminho):
        return vals
    with open(caminho, encoding="utf-8") as f:
        for linha in f:
            linha = linha.strip()
            if not linha or linha.startswith("#") or "=" not in linha:
                continue
            k, v = linha.split("=", 1)
            k = k.strip()
            if k.startswith("export "):
                k = k[7:].strip()
            vals[k] = v.strip().strip('"').strip("'")
    return vals


def log(msg):
    sys.stderr.write("[%s] %s\n" % (_dt.datetime.now().strftime("%H:%M:%S"), msg))
    sys.stderr.flush()
