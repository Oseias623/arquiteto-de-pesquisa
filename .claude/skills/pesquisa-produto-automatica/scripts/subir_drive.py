#!/usr/bin/env python3
"""Sobe a planilha da pesquisa e os vídeos de referência para a pasta do produto no Google Drive.

Uso:
  python3 subir_drive.py --pasta-id ID_DA_PASTA_DO_PRODUTO --planilha "Pesquisa ....xlsx" [--videos pasta/videos] [--sem-converter]

- Autenticação: token do gcloud (`gcloud auth login --enable-gdrive-access`, uma vez, com a conta que é editora da pasta).
- A planilha sobe convertida em Planilha Google (use --sem-converter para manter .xlsx).
  --atualizar ID_DA_PLANILHA: substitui o conteúdo de uma Planilha Google existente (mesmo link; a versão
  anterior fica no Histórico de versões do Sheets). Use quando já houver pesquisa do mesmo produto e ângulo.
  Sem --atualizar, se já existir uma com o mesmo nome na pasta, cria outra com sufixo de data e hora.
- Vídeos (*.mp4) vão para a subpasta "Referências (vídeos)" (criada se faltar); os que já existirem com o mesmo nome são pulados.
- Saída: JSON com o link de cada arquivo enviado e o que foi pulado ou falhou.
"""
import argparse
import datetime
import glob
import json
import os
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request

API = "https://www.googleapis.com/drive/v3/files"
UPLOAD = "https://www.googleapis.com/upload/drive/v3/files"
SUBPASTA_VIDEOS = "Referências (vídeos)"
XLSX = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
SHEET = "application/vnd.google-apps.spreadsheet"
FOLDER = "application/vnd.google-apps.folder"


def token():
    try:
        return subprocess.check_output(["gcloud", "auth", "print-access-token"], text=True,
                                       stderr=subprocess.DEVNULL).strip()
    except (OSError, subprocess.CalledProcessError):
        sys.exit("sem token: rode `gcloud auth login --enable-gdrive-access` com a conta editora da pasta")


def chamar(tok, metodo, url, corpo=None, tipo="application/json"):
    req = urllib.request.Request(url, data=corpo, method=metodo,
                                 headers={"Authorization": "Bearer " + tok, "Content-Type": tipo})
    with urllib.request.urlopen(req, timeout=600) as r:
        return json.loads(r.read().decode() or "{}")


def listar(tok, pai, nome=None, mime=None):
    q = ["'%s' in parents" % pai, "trashed = false"]
    if nome:
        q.append("name = '%s'" % nome.replace("\\", "\\\\").replace("'", "\\'"))
    if mime:
        q.append("mimeType = '%s'" % mime)
    url = API + "?" + urllib.parse.urlencode({"q": " and ".join(q), "fields": "files(id,name,webViewLink)",
                                              "supportsAllDrives": "true", "includeItemsFromAllDrives": "true"})
    return chamar(tok, "GET", url).get("files", [])


def subir(tok, caminho, pai, nome, mime_origem, mime_destino=None):
    meta = {"name": nome, "parents": [pai]}
    if mime_destino:
        meta["mimeType"] = mime_destino
    limite = "subir-drive-limite"
    with open(caminho, "rb") as f:
        dados = f.read()
    corpo = (("--%s\r\nContent-Type: application/json; charset=UTF-8\r\n\r\n" % limite).encode()
             + json.dumps(meta).encode()
             + ("\r\n--%s\r\nContent-Type: %s\r\n\r\n" % (limite, mime_origem)).encode()
             + dados + ("\r\n--%s--" % limite).encode())
    url = UPLOAD + "?uploadType=multipart&supportsAllDrives=true&fields=id,name,webViewLink"
    return chamar(tok, "POST", url, corpo, "multipart/related; boundary=" + limite)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pasta-id", required=True)
    ap.add_argument("--planilha")
    ap.add_argument("--videos")
    ap.add_argument("--sem-converter", action="store_true")
    ap.add_argument("--atualizar", metavar="ID_DA_PLANILHA")
    a = ap.parse_args()
    tok = token()
    rel = {"planilha": None, "videos": [], "pulados": [], "falhas": []}

    if a.planilha and a.atualizar:
        with open(a.planilha, "rb") as f:
            dados = f.read()
        url = UPLOAD + "/" + a.atualizar + "?uploadType=media&supportsAllDrives=true&fields=id,name,webViewLink,modifiedTime"
        try:
            rel["planilha"] = chamar(tok, "PATCH", url, dados, XLSX)
        except urllib.error.HTTPError as e:
            rel["falhas"].append({"arquivo": a.planilha, "erro": "%s %s" % (e.code, e.read().decode()[:300])})
    elif a.planilha:
        nome = os.path.splitext(os.path.basename(a.planilha))[0]
        if a.sem_converter:
            nome += ".xlsx"
        if listar(tok, a.pasta_id, nome):
            nome += " (" + datetime.datetime.now().strftime("%Y-%m-%d %H%M") + ")"
        try:
            rel["planilha"] = subir(tok, a.planilha, a.pasta_id, nome, XLSX, None if a.sem_converter else SHEET)
        except urllib.error.HTTPError as e:
            rel["falhas"].append({"arquivo": a.planilha, "erro": "%s %s" % (e.code, e.read().decode()[:300])})

    if a.videos:
        achadas = listar(tok, a.pasta_id, SUBPASTA_VIDEOS, FOLDER)
        if achadas:
            sub = achadas[0]["id"]
        else:
            sub = chamar(tok, "POST", API + "?supportsAllDrives=true&fields=id",
                         json.dumps({"name": SUBPASTA_VIDEOS, "mimeType": FOLDER, "parents": [a.pasta_id]}).encode())["id"]
        existentes = {f["name"] for f in listar(tok, sub)}
        for v in sorted(glob.glob(os.path.join(a.videos, "*.mp4"))):
            nome = os.path.basename(v)
            if nome in existentes:
                rel["pulados"].append(nome)
                continue
            try:
                rel["videos"].append(subir(tok, v, sub, nome, "video/mp4"))
            except urllib.error.HTTPError as e:
                rel["falhas"].append({"arquivo": nome, "erro": "%s %s" % (e.code, e.read().decode()[:300])})

    print(json.dumps(rel, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
