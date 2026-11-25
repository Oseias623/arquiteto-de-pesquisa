#!/usr/bin/env python3
"""Acrescenta referências APROVADAS pelo Oséias na aba Índice do swipe (formato de references/planilha.md, Apêndice).

Uso:
  python3 adicionar_ao_swipe.py swipe.xlsx entrada.json [saida.xlsx] [--reparar-ids]
    swipe.xlsx   cópia local do "Swipe - Índice" (se não existir, cria a aba Índice vazia com o cabeçalho)
    saida.xlsx   padrão: sobrescreve swipe.xlsx
    --reparar-ids  converte para texto os IDs da coluna W que estão como número, usando o ?id= do link (V)
                   (o link é a fonte confiável; ID com 16+ dígitos guardado como número já perdeu dígitos)

Formato do JSON:
{
  "adicionado_em": "2026-11-24",             # opcional (padrão: hoje)
  "linhas": [{
    "nicho": "Skincare - manchas", "marca_produto": "Lumi Radiance (Farmasi)", "pagina": "Arencia Global",
    "pais": "EUA", "inicio": "2026-05-15", "status": "Ativo (24/11/2026)",    # status padrão: "Ativo (<adicionado_em>)"
    "formato": "", "gancho_verbal": "", "gancho_visual": "", "estrutura": "", "angulo": "", "avatar": "",
    "prova": "", "oferta_cta": "", "destino": "", "aprender": "", "nao_transportar": "", "como_visto": "",
    "id": "1615613962848342",                 # SEMPRE string. "link" opcional (gerado do id)
    "midia_drive": "", "tags": "a; b; c"
  }]
}
Garantias: ID (W) gravado como texto com formato "@"; datas B e G como texto ISO (aaaa-mm-dd), que é o que a
fórmula do Índice espera (=IF(G="","",TODAY()-DATEVALUE(G))); H sempre com essa fórmula (nunca número fixo);
texto que começa com = + - @ ganha quotePrefix; ID já presente em V/W é pulado.
"""
import json
import os
import re
import sys
from datetime import date

from openpyxl import Workbook, load_workbook
from openpyxl.styles import Alignment, Font, PatternFill

CAB = ["#", "Adicionado em", "Nicho", "Marca / produto", "Página que anuncia", "País da busca", "Início",
       "Dias no ar", "Status (última checagem)", "Formato", "Gancho verbal", "Gancho visual",
       "Estrutura (sequência)", "Ângulo / desejo / objeção", "Avatar", "Prova", "Oferta e CTA", "Destino",
       "O que aprender", "Não transportar sem prova", "Como foi visto", "Link Ad Library", "ID", "Mídia no Drive",
       "Tags"]
CHAVES = [None, "adicionado_em", "nicho", "marca_produto", "pagina", "pais", "inicio", None, "status", "formato",
          "gancho_verbal", "gancho_visual", "estrutura", "angulo", "avatar", "prova", "oferta_cta", "destino",
          "aprender", "nao_transportar", "como_visto", "link", "id", "midia_drive", "tags"]
FONTE = Font(name="Arial", size=10)
FONTE_LINK = Font(name="Arial", size=10, color="FF0000FF")
AL = Alignment(wrap_text=True, vertical="top")
ID_RE = re.compile(r"[?&]id=(\d+)")


def criar(caminho):
    wb = Workbook()
    ws = wb.active
    ws.title = "Índice"
    for j, h in enumerate(CAB, 1):
        c = ws.cell(row=1, column=j, value=h)
        c.fill = PatternFill("solid", fgColor="FFEDEDED")
        c.font = Font(name="Arial", size=10, bold=True)
        c.alignment = Alignment(wrap_text=True)
    for col, w in {"A": 5.1, "B": 15.1, "D": 22.6, "E": 15.1, "J": 32.6, "V": 20.1}.items():
        ws.column_dimensions[col].width = w
    ws.freeze_panes = "E2"
    return wb


def texto(c, v, forcar_texto=False):
    if v is None or v == "":
        c.value = None
        return
    s = str(v)
    c.value = s
    c.data_type = "s"
    if s[:1] in "=+-@":
        c.quotePrefix = True
    if forcar_texto:
        c.number_format = "@"
    c.font = FONTE_LINK if re.match(r"^https?://\S+$", s) else FONTE
    if c.font is FONTE_LINK:
        c.hyperlink = s
    c.alignment = AL


def id_texto(v):
    if isinstance(v, float):
        raise ValueError(f"ID veio como float ({v!r}): dígitos já perdidos. Mande como string.")
    s = str(v).strip()
    if not s.isdigit():
        raise ValueError(f"ID inválido: {v!r}")
    return s


def ids_existentes(ws):
    vistos = set()
    for r in range(2, ws.max_row + 1):
        w, v = ws.cell(r, 23).value, ws.cell(r, 22).value
        if w not in (None, ""):
            vistos.add(str(int(w)) if isinstance(w, float) else str(w).strip())
        m = ID_RE.search(str(v or ""))
        if m:
            vistos.add(m[1])
    return vistos


def ultima_linha(ws):
    # H vem pré-preenchida com fórmula até ~500: ignorar H ao procurar a última linha usada.
    for r in range(ws.max_row, 1, -1):
        if any(ws.cell(r, c).value not in (None, "") for c in range(1, 26) if c != 8):
            return r
    return 1


def reparar_ids(ws):
    rel = []
    for r in range(2, ultima_linha(ws) + 1):
        c = ws.cell(r, 23)
        m = ID_RE.search(str(ws.cell(r, 22).value or ""))
        if isinstance(c.value, (int, float)) or (c.value in (None, "") and m):
            antigo = c.value
            if m:
                texto(c, m[1], forcar_texto=True)
                if antigo not in (None, "") and str(int(antigo)) != m[1]:
                    rel.append(f"linha {r}: ID numérico {int(antigo)} difere do link ({m[1]}); ficou o do link")
                else:
                    rel.append(f"linha {r}: ID {m[1]} convertido para texto")
            else:
                rel.append(f"linha {r}: ID numérico {antigo!r} sem link para conferir; NÃO alterado")
    return rel


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if len(args) not in (2, 3):
        sys.exit(__doc__)
    swipe, entrada = args[0], args[1]
    saida = args[2] if len(args) == 3 else swipe
    wb = load_workbook(swipe) if os.path.exists(swipe) else criar(swipe)
    ws = wb["Índice"]
    if "--reparar-ids" in sys.argv:
        for linha in reparar_ids(ws):
            print("REPARO:", linha)
    with open(entrada, encoding="utf-8") as f:
        spec = json.load(f)
    hoje = str(spec.get("adicionado_em") or date.today().isoformat())[:10]
    vistos = ids_existentes(ws)
    r = ultima_linha(ws)
    nums = [ws.cell(i, 1).value for i in range(2, r + 1)]
    n = int(max([x for x in nums if isinstance(x, (int, float))] or [0]))
    add = 0
    for ln in spec.get("linhas", []):
        idt = id_texto(ln["id"]) if ln.get("id") not in (None, "") else None
        if not idt and ln.get("link"):
            m = ID_RE.search(ln["link"])
            idt = m[1] if m else None
        if idt and idt in vistos:
            print(f"PULADO: ID {idt} já está no swipe")
            continue
        r += 1
        n += 1
        add += 1
        vals = dict(ln)
        vals["adicionado_em"] = hoje
        vals.setdefault("status", f"Ativo ({date.fromisoformat(hoje):%d/%m/%Y})")
        vals["inicio"] = str(ln["inicio"])[:10] if ln.get("inicio") else None
        vals["link"] = ln.get("link") or (f"https://www.facebook.com/ads/library/?id={idt}" if idt else None)
        vals["id"] = idt
        ws.cell(r, 1, n).font = FONTE
        ws.cell(r, 1).alignment = AL
        for j, k in enumerate(CHAVES, 1):
            if k is None:
                continue
            texto(ws.cell(r, j), vals.get(k), forcar_texto=(k == "id"))
        h = ws.cell(r, 8)
        h.value = f'=IF(G{r}="","",TODAY()-DATEVALUE(G{r}))'
        h.number_format = "0"
        h.font, h.alignment = FONTE, AL
        if idt:
            vistos.add(idt)
    wb.save(saida)
    print(f"ok: {add} linha(s) acrescentada(s) em {saida}")


if __name__ == "__main__":
    main()
