#!/usr/bin/env python3
"""Monta a planilha da pesquisa (.xlsx) no padrão do Oséias a partir de um JSON.

Uso:  python3 montar_planilha.py entrada.json saida.xlsx [--estrito]
      (--estrito: sai com código 1 se houver avisos de verificação)

O ESQUEMA (nomes e ordem das 10 abas, cabeçalhos da linha 4, cores, colunas
amarelas, fórmulas, dropdowns, blocos de contadores, larguras, freeze) está
embutido aqui e segue `references/planilha.md`. O JSON traz só o conteúdo.

Formato do JSON
---------------
{
  "produto": "Lumi",                  # nome curto -> "Serve para o Lumi?", "O que modelar para o Lumi"
  "produto_com_artigo": "o Lumi",     # opcional (padrão "o <produto>")
  "marca": "Farmasi",                 # marca do produto anunciado
  "marca_com_artigo": "a Farmasi",    # opcional (padrão "a <marca>") -> "Alerta de compliance para a Farmasi"
  "angulo": "dark spots",             # ângulo/dor da pesquisa (vai nos títulos padrão)
  "nicho": "manchas",                 # nicho em palavras (títulos padrão)
  "pais": "EUA",                      # país da Biblioteca
  "idioma": "inglês",                 # idioma das frases de cliente (título da aba Voz do cliente)
  "data_consulta": "2026-11-24",      # ISO; vira =DATE(...) nas abas A, Candidatos e Amostra
  "pais_codigo": "US",                # opcional: código do país na Biblioteca (link da página dos concorrentes;
                                      # sem ele o link usa country=ALL)
  "abas": {
    "produto":      {"nome": "Produto Lumi Radiance",          # padrão "Produto <produto>"
                     "linhas": [{"campo": "", "informacao": "", "fonte": ""}],
                     "secoes": [{"titulo": "O que muda na pesquisa", "linhas": [{"campo": "Continua valendo", "informacao": "", "fonte": ""}]},
                                {"titulo": "Pendências de pesquisa", "linhas": [{"campo": 1, "informacao": ""}]}]},
    "referencias":  {"linhas": [{"marca", "link" | "id", "formato", "tempo_rodando" (opcional: gerado de inicio),
                                 "inicio" (ISO, obrigatório), "gancho", "angulo", "mecanismo",
                                 "por_que_funciona" (AMARELA: deixar vazio), "evidencia",
                                 "formato_cat", "angulo_cat", "prova_cat", "oferta_cat", "serve" (Sim/Adaptar/Não)}],
                     "categorias": {"formato": [], "angulo": [], "prova": [], "oferta": []}},
    "transcricoes": {"linhas": [{"link" | "id", "marca", "video_drive", "duracao", "formato", "gancho_visual",
                                 "gancho_falado", "texto_tela", "body", "estrutura", "angulo", "mecanismo", "prova",
                                 "cta_falado", "cta_copy", "destino", "copy", "modelar" (amarela), "nao_transportar", "cobertura"}]},
    "candidatos":   {"linhas": [{"anunciante", "titulo", "link" | "id", "inicio", "observacao", "serve"}]},
    "amostra":      {"concorrentes": [{"marca", "produto", "preco", "mecanismo", "por_que",   # até 5 (quadro U4)
                                       "page_id" | "link_pagina"}],      # page_id -> link view_all_page_id
                     "linhas": [{"marca", "titulo", "link" | "id", "inicio", "formato_cat", "angulo_cat", "mecanismo_cat",
                                 "gancho", "angulo_desc" (amarela), "mecanismo_desc" (amarela), "prova", "oferta_cta",
                                 "alerta_compliance", "observacoes", "serve", "prova_cat",
                                 "modelar" (amarela: o que modelar deste concorrente; vazio)}],
                     "categorias": {"formato": [], "angulo": [], "mecanismo": [], "prova": []}},
                    # aba "Amostra concorrentes"; a chave antiga "amostra_3_marcas" (ou "amostra_concorrentes")
                    # também é aceita. Linhas antigas sem prova_cat/modelar continuam válidas.
    "padroes":      {"linhas": [{"secao": "B" | "C" | "D" | "E", "item": 1 | "extra", "padrao", "evidencia",
                                 "sua_versao" (amarela: vazio), "serve"}]},
    "big_ideas":    {"linhas": [{"item": "Lacuna 1", "pista", "evidencia", "compliance", "sua_versao" (amarela: vazio)}]},
    "voz_cliente":  {"linhas": [{"frase", "tema", "fonte", "sobre": "Genérico" | "Marca <marca>"}, {"separador": "--- Coleta ... ---"}]},
    "ia_travou":    {"linhas": [{"fato", "como_resolvido"}]},
    "fontes":       {"linhas": [{"fonte", "url"}]}
  }
}
Em qualquer aba também valem:
  "titulo" / "legenda"  -> sobrescrevem as linhas 1 e 2 (há textos padrão do gabarito);
  "celulas": {"E2": "texto", "X9": {"formula": "=..."}} -> células avulsas (texto nunca vira fórmula;
             fórmula só com {"formula": ...}).
Linhas podem ser dict (chaves acima) ou lista na ordem das colunas de dados. "#" é numerado sozinho.

Garantias
---------
* Texto do JSON nunca vira fórmula: células de dados são gravadas como string. Texto que começa com
  = + - @ ganha quotePrefix (o apóstrofo do Excel/Sheets: aparece sem o ' na célula e é lido como texto).
* IDs da Meta: sempre string + formato "@" (texto). ID numérico float é recusado (já perdeu dígitos).
  Sequência só de dígitos com 12+ caracteres também é forçada a texto. Ao importar no Google Sheets a
  célula continua texto (não vira 2,54937E+15).
* Fórmulas em sintaxe .xlsx (separador ","). O Google Sheets converte para ";" sozinho ao importar.
"""
import json
import re
import sys
import unicodedata
from datetime import date

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import column_index_from_string
from openpyxl.worksheet.datavalidation import DataValidation

AZUL = "FF1E3863"
AMARELO = "FFFFF2CC"
F_AZUL = PatternFill("solid", fgColor=AZUL)
F_AMARELO = PatternFill("solid", fgColor=AMARELO)
FONTE = Font(name="Arial", size=10)
FONTE_NEG = Font(name="Arial", size=10, bold=True)
FONTE_TITULO = Font(name="Arial", size=11, bold=True)
FONTE_CAB = Font(name="Arial", size=10, bold=True, color="FFFFFFFF")
FONTE_LINK = Font(name="Arial", size=10, color="FF0000FF")
AL_DADOS = Alignment(wrap_text=True, vertical="top")
AL_CAB = Alignment(wrap_text=True, vertical="top")
FIM = 1000          # fim dos intervalos das fórmulas de contagem ($5:$1000)
FIM_DV = 200        # fim dos dropdowns (5:200), como no gabarito
LEGENDA = "Legenda: células amarelas = você preenche, com suas palavras. O resto é matéria-prima com fonte."
SERVE = ["Sim", "Adaptar", "Não"]
PROIBIDAS = ["vencedor", "campeao", "escalado", "lucrativo", "perdedor", "domina o nicho", "saturado"]
URL_RE = re.compile(r"^https?://\S+$")
SECOES_PADROES = {"B": "B. Ângulo", "C": "C. Formato", "D": "D. Gancho", "E": "E. Mecanismo"}

avisos = []


# --------------------------------------------------------------------------- utilidades
def iso(d):
    return date.fromisoformat(str(d)[:10])


def f_date(d):
    d = iso(d)
    return f"DATE({d.year},{d.month},{d.day})"


def link_meta(v):
    return f"https://www.facebook.com/ads/library/?id={id_texto(v)}"


def id_texto(v):
    if isinstance(v, float):
        raise ValueError(f"ID da Meta veio como número float ({v!r}): dígitos já perdidos. Mande como string.")
    s = str(v).strip()
    if not s.isdigit():
        raise ValueError(f"ID da Meta inválido: {v!r}")
    return s


def sem_acento(s):
    return "".join(c for c in unicodedata.normalize("NFD", s.lower()) if unicodedata.category(c) != "Mn")


def nome_aba(s):
    return re.sub(r"[\[\]:*?/\\]", "", s)[:31]


def texto(ws, ref, v, fonte=FONTE, al=AL_DADOS, fill=None, forcar_texto=False):
    """Grava um valor de conteúdo. Strings nunca viram fórmula."""
    c = ws[ref]
    if v is None or v == "":
        c.value = None
    elif isinstance(v, bool):
        c.value = "Sim" if v else "Não"
    elif isinstance(v, (int, float)) and not forcar_texto:
        c.value = v
    else:
        s = str(v)
        c.value = s
        c.data_type = "s"
        if s[:1] in "=+-@":
            c.quotePrefix = True
        if forcar_texto or (s.isdigit() and len(s) >= 12):
            c.number_format = "@"
        if URL_RE.match(s):
            c.hyperlink = s
            fonte = FONTE_LINK
    c.font = fonte
    if al is not None:
        c.alignment = al
    if fill is not None:
        c.fill = fill
    return c


def formula(ws, ref, f, nf=None, fonte=FONTE, al=AL_DADOS, fill=None):
    c = ws[ref]
    c.value = f if f.startswith("=") else "=" + f
    c.font = fonte
    if al is not None:
        c.alignment = al
    if nf:
        c.number_format = nf
    if fill is not None:
        c.fill = fill
    return c


def cabecalho(ws, linha, col_ini, nomes, wrap=True):
    for j, n in enumerate(nomes):
        c = ws.cell(row=linha, column=col_ini + j, value=n)
        c.fill, c.font = F_AZUL, FONTE_CAB
        c.alignment = Alignment(wrap_text=wrap, vertical="top")


def titulo(ws, aba, padrao_titulo, padrao_legenda, negrito=False):
    texto(ws, "A1", aba.get("titulo", padrao_titulo), fonte=FONTE_TITULO if negrito else FONTE, al=None)
    leg = aba.get("legenda", padrao_legenda)
    if leg:
        texto(ws, "A2", leg, al=None)


def larguras(ws, d):
    for col, w in d.items():
        ws.column_dimensions[col].width = w


def dropdown(ws, col, opcoes):
    lista = ",".join(opcoes)
    if len(lista) > 255:
        avisos.append(f"{ws.title}: lista da coluna {col} passa de 255 caracteres (limite do Excel)")
    if any('"' in o for o in opcoes):
        raise ValueError(f"{ws.title}: opção de dropdown com aspas na coluna {col}")
    dv = DataValidation(type="list", formula1=f'"{lista}"', allow_blank=True)
    ws.add_data_validation(dv)
    dv.add(f"{col}5:{col}{FIM_DV}")


def celulas_avulsas(ws, aba):
    for ref, v in aba.get("celulas", {}).items():
        if isinstance(v, dict) and "formula" in v:
            formula(ws, ref, v["formula"], nf=v.get("formato"), al=None)
        else:
            texto(ws, ref, v, al=None)


def normalizar(linhas, chaves):
    out = []
    for ln in linhas:
        if isinstance(ln, dict):
            out.append(ln)
        else:
            out.append({k: (ln[i] if i < len(ln) else None) for i, k in enumerate(chaves)})
    return out


def link_da(ln, aba, i):
    if ln.get("link"):
        return ln["link"]
    if ln.get("id") not in (None, ""):
        return link_meta(ln["id"])
    avisos.append(f"{aba}: linha {i} sem link")
    return None


def categorias(aba, chave, linhas, campo):
    lista = list(aba.get("categorias", {}).get(chave) or [])
    for ln in linhas:
        v = ln.get(campo)
        if v and v not in lista:
            if aba.get("categorias", {}).get(chave):
                avisos.append(f"categoria '{v}' ({campo}) não estava na lista; acrescentada")
            lista.append(v)
    return lista


def bloco_contador(ws, linha, col, rotulo, titulo_pct, opcoes, col_dados, ref_total):
    """Bloco cabeçalho azul (rótulo | Anúncios | %) + COUNTIF/percentual. Devolve a próxima linha livre."""
    c0, c1, c2 = col
    cabecalho(ws, linha, column_index_from_string(c0), [rotulo, "Anúncios", titulo_pct], wrap=False)
    for k, op in enumerate(opcoes, 1):
        r = linha + k
        texto(ws, f"{c0}{r}", op, al=None)
        formula(ws, f"{c1}{r}", f"=COUNTIF(${col_dados}$5:${col_dados}${FIM},{c0}{r})", al=None)
        formula(ws, f"{c2}{r}", f"=IF({ref_total}=0,0,{c1}{r}/{ref_total})", nf="0%", al=None)
    return linha + len(opcoes) + 2


# --------------------------------------------------------------------------- abas
def aba_produto(wb, spec, aba):
    ws = wb.create_sheet(nome_aba(aba.get("nome") or f"Produto {spec['produto']}"))
    titulo(ws, aba, f"Produto anunciado no ângulo {spec.get('angulo', '')}: {spec['produto']}",
           f"O que está aqui é o texto oficial d{spec['_marca_art']}. Só use no anúncio o que está nesta aba.", negrito=True)
    cabecalho(ws, 4, 1, ["Campo", "Informação", "Fonte"])
    r = 5
    for ln in normalizar(aba.get("linhas", []), ["campo", "informacao", "fonte"]):
        for col, k in zip("ABC", ["campo", "informacao", "fonte"]):
            texto(ws, f"{col}{r}", ln.get(k))
        r += 1
    for sec in aba.get("secoes", []):
        r += 1
        texto(ws, f"A{r}", sec["titulo"], fonte=FONTE_NEG)
        r += 1
        for ln in normalizar(sec.get("linhas", []), ["campo", "informacao", "fonte"]):
            for col, k in zip("ABC", ["campo", "informacao", "fonte"]):
                texto(ws, f"{col}{r}", ln.get(k))
            r += 1
    larguras(ws, {"A": 21.4, "B": 70.1, "C": 47.6})
    ws.freeze_panes = "A5"
    celulas_avulsas(ws, aba)


def aba_referencias(wb, spec, aba):
    ws = wb.create_sheet("A - Anúncios de referência")
    data_c = iso(spec["data_consulta"])
    serve = f"Serve para {spec['_prod_art']}?"
    titulo(ws, aba,
           f"A. Anúncios de referência para o ângulo {spec.get('angulo', '')} (Biblioteca de Anúncios, "
           f"{spec.get('pais', '')}, consulta em {data_c:%d/%m/%Y}). Mínimo de 10 anúncios, com dados categorizados "
           "nas colunas M a R e contagem a partir da coluna T. Mínimos de texto: gancho 20 · ângulo 30 · "
           "mecanismo 30 · por que funciona 200 caracteres.", LEGENDA)
    texto(ws, "M2", "Data da consulta", al=None)
    formula(ws, "N2", "=" + f_date(data_c), nf="dd/mm/yyyy", al=None)
    cabecalho(ws, 4, 1, ["#", "Link (Biblioteca)", "Marca", "Formato (assistir e escolher)", "Tempo rodando",
                         "Gancho transcrito (assistir)", "Ângulo (proposta pelo texto; confirmar assistindo)",
                         "Mecanismo (confirmar assistindo)",
                         "Por que você acha que funciona (mín. 200): SEU raciocínio", "Evidência de continuidade",
                         "Caracteres: gancho (mín. 20)", "Caracteres: por que funciona (mín. 200)", "Dias ativos",
                         "Formato (categoria)", "Ângulo (categoria)", "Prova (categoria)", "Oferta (categoria)", serve])
    chaves = ["marca", "link", "formato", "tempo_rodando", "inicio", "gancho", "angulo", "mecanismo",
              "por_que_funciona", "evidencia", "formato_cat", "angulo_cat", "prova_cat", "oferta_cat", "serve"]
    linhas = normalizar(aba.get("linhas", []), chaves)
    if len(linhas) < 10:
        avisos.append(f"A - Anúncios de referência: {len(linhas)} referências (mínimo 10)")
    for i, ln in enumerate(linhas, 1):
        r = 4 + i
        texto(ws, f"A{r}", ln.get("#", i))
        texto(ws, f"B{r}", link_da(ln, "A", i))
        texto(ws, f"C{r}", ln.get("marca"))
        texto(ws, f"D{r}", ln.get("formato"))
        tempo = ln.get("tempo_rodando")
        if not tempo and ln.get("inicio"):
            ini = iso(ln["inicio"])
            tempo = f"Desde {ini:%d/%m/%Y} (~{(data_c - ini).days} dias)"
        texto(ws, f"E{r}", tempo)
        texto(ws, f"F{r}", ln.get("gancho"))
        texto(ws, f"G{r}", ln.get("angulo"))
        texto(ws, f"H{r}", ln.get("mecanismo"))
        texto(ws, f"I{r}", ln.get("por_que_funciona"), fill=F_AMARELO)
        texto(ws, f"J{r}", ln.get("evidencia"))
        formula(ws, f"K{r}", f"=LEN(F{r})")
        formula(ws, f"L{r}", f"=LEN(I{r})")
        if ln.get("inicio"):
            formula(ws, f"M{r}", f"=$N$2-{f_date(ln['inicio'])}", nf="0")
        else:
            avisos.append(f"A: linha {i} sem data de início")
        for col, k in zip("NOPQR", ["formato_cat", "angulo_cat", "prova_cat", "oferta_cat", "serve"]):
            texto(ws, f"{col}{r}", ln.get(k))
        if ln.get("serve") and ln["serve"] not in SERVE:
            avisos.append(f"A: linha {i} 'serve' = {ln['serve']!r} (use Sim/Adaptar/Não)")
    cats = {k: categorias(aba, k, linhas, f"{k}_cat") for k in ["formato", "angulo", "prova", "oferta"]}
    for col, k in zip("NOPQ", ["formato", "angulo", "prova", "oferta"]):
        dropdown(ws, col, cats[k])
    dropdown(ws, "R", SERVE)
    # bloco de contadores (T:V)
    texto(ws, "T1", "Dados das referências", fonte=FONTE_NEG, al=None)
    resumo = [("Referências", f"=COUNTA($A$5:$A${FIM})", None),
              ("Média de dias ativos", f"=AVERAGE($M$5:$M${FIM})", "0"),
              ("Mediana de dias ativos", f"=MEDIAN($M$5:$M${FIM})", "0"),
              ("Referências com mais de 100 dias", f'=COUNTIF($M$5:$M${FIM},">100")', None)]
    for k, (rot, f, nf) in enumerate(resumo, 2):
        texto(ws, f"T{k}", rot, fonte=FONTE_NEG, al=None)
        formula(ws, f"U{k}", f, nf=nf, al=None)
    lin = 7
    for rot, k, col in [("Formato", "formato", "N"), ("Ângulo", "angulo", "O"), ("Prova", "prova", "P"),
                        ("Oferta", "oferta", "Q")]:
        lin = bloco_contador(ws, lin, "TUV", rot, "% das referências", cats[k], col, "$U$2")
    bloco_contador(ws, lin, "TUV", serve, "% das referências", SERVE, "R", "$U$2")
    larguras(ws, {"A": 5.1, "B": 27.6, "K": 13.9, "M": 10.1, "N": 21.4, "S": 3.9, "T": 30.1, "U": 13.9})
    ws.freeze_panes = "A5"
    celulas_avulsas(ws, aba)


def aba_transcricoes(wb, spec, aba):
    ws = wb.create_sheet("Transcrições")
    titulo(ws, aba, "Transcrições dos vídeos de referência: um anúncio por linha, desmontado em gancho, body, "
                    f"ângulo, CTA e o que modelar para {spec['_prod_art']}.",
           "Declare na coluna Cobertura o que foi visto e ouvido (áudio, legendas, quadros).", negrito=True)
    cab = ["#", "Link (Biblioteca)", "Marca / quem fala", "Vídeo no Drive", "Duração", "Formato",
           "Gancho visual (0 a 3 s)", "Gancho falado", "Texto fixo na tela", "Body (transcrição completa)",
           "Estrutura (tempo → bloco → função)", "Ângulo", "Mecanismo", "Prova", "CTA falado",
           "CTA da copy / botão", "Destino", "Copy do anúncio", f"O que modelar para {spec['_prod_art']}",
           "Não transportar", "Cobertura"]
    cabecalho(ws, 4, 1, cab)
    chaves = ["link", "marca", "video_drive", "duracao", "formato", "gancho_visual", "gancho_falado", "texto_tela",
              "body", "estrutura", "angulo", "mecanismo", "prova", "cta_falado", "cta_copy", "destino", "copy",
              "modelar", "nao_transportar", "cobertura"]
    for i, ln in enumerate(normalizar(aba.get("linhas", []), chaves), 1):
        r = 4 + i
        texto(ws, f"A{r}", ln.get("#", i))
        texto(ws, f"B{r}", link_da(ln, "Transcrições", i))
        for j, k in enumerate(chaves[1:], 3):
            col = ws.cell(row=r, column=j).column_letter
            texto(ws, f"{col}{r}", ln.get(k), fill=F_AMARELO if k == "modelar" else None)
        if not ln.get("cobertura"):
            avisos.append(f"Transcrições: linha {i} sem cobertura declarada")
    larguras(ws, {"A": 4.5, "B": 27.6, "E": 8.9, "F": 27.6, "J": 47.6, "L": 27.6})
    ws.freeze_panes = "D5"
    celulas_avulsas(ws, aba)


def aba_candidatos(wb, spec, aba):
    ws = wb.create_sheet("Candidatos (Biblioteca)")
    titulo(ws, aba, f"Somente anúncios ATIVOS há MAIS DE 100 DIAS sobre {spec.get('nicho', '')} (Biblioteca de "
                    f"Anúncios, {spec.get('pais', '')}).", "")
    texto(ws, "A3", "Data da consulta", al=None)
    formula(ws, "B3", "=" + f_date(spec["data_consulta"]), nf="dd/mm/yyyy", al=None)
    cabecalho(ws, 4, 1, ["Anunciante", "Título do anúncio (ou 1ª linha quando não há título)", "Link",
                         "Data de início", "Tempo no ar (dias)", "Observação", f"Serve para {spec['_prod_art']}?"])
    chaves = ["anunciante", "titulo", "link", "inicio", "observacao", "serve"]
    for i, ln in enumerate(normalizar(aba.get("linhas", []), chaves), 1):
        r = 4 + i
        texto(ws, f"A{r}", ln.get("anunciante"))
        texto(ws, f"B{r}", ln.get("titulo"))
        texto(ws, f"C{r}", link_da(ln, "Candidatos", i))
        if ln.get("inicio"):
            formula(ws, f"D{r}", "=" + f_date(ln["inicio"]), nf="dd/mm/yyyy")
            formula(ws, f"E{r}", f"=$B$3-D{r}", nf="0")
        else:
            avisos.append(f"Candidatos: linha {i} sem data de início")
        texto(ws, f"F{r}", ln.get("observacao"))
        texto(ws, f"G{r}", ln.get("serve"))
    larguras(ws, {"A": 27.6, "D": 13.9, "F": 27.6})
    ws.freeze_panes = "A5"
    celulas_avulsas(ws, aba)


AMOSTRA = "Amostra concorrentes"
AMOSTRA_SINONIMOS = ["amostra", "amostra_concorrentes", "amostra_3_marcas", AMOSTRA, "Amostra 3 marcas"]
MAX_CONCORRENTES = 5


def link_pagina(spec, c):
    if c.get("link_pagina"):
        return c["link_pagina"]
    if c.get("page_id") not in (None, ""):
        return ("https://www.facebook.com/ads/library/?active_status=active&ad_type=all"
                f"&country={spec.get('pais_codigo') or 'ALL'}&view_all_page_id={id_texto(c['page_id'])}"
                "&search_type=page&media_type=all")
    avisos.append(f"{AMOSTRA}: concorrente {c.get('marca')!r} sem página na Biblioteca (page_id/link_pagina)")
    return None


def aba_amostra(wb, spec, aba):
    ws = wb.create_sheet(AMOSTRA)
    titulo(ws, aba, f"Amostra dos concorrentes diretos: todos os anúncios ativos sobre {spec.get('nicho', '')} de até "
                    f"{MAX_CONCORRENTES} concorrentes (Biblioteca de Anúncios Meta, {spec.get('pais', '')}).", None)
    texto(ws, "A2", "Data da consulta", al=None)
    formula(ws, "C2", "=" + f_date(spec["data_consulta"]), nf="dd/mm/yyyy", al=None)
    texto(ws, "E2", "Colunas G, H, I e R têm lista suspensa para contar os padrões no quadro ao lado (coluna U em "
                    "diante).", al=None)
    cabecalho(ws, 4, 1, ["#", "Marca", "Título na Biblioteca", "Link", "Ativo desde", "Dias ativos",
                         "Formato (categoria)", "Ângulo (categoria)", "Mecanismo (categoria)",
                         "Gancho transcrito (1ª frase do texto)", "Ângulo (descrição)", "Mecanismo (descrição)",
                         "Prova / autoridade usada", "Oferta / CTA",
                         f"Alerta de compliance para {spec['_marca_art']}", "Observações",
                         f"Serve para {spec['_prod_art']}?", "Prova (categoria)", "O que modelar deste concorrente"])
    chaves = ["marca", "titulo", "link", "inicio", "formato_cat", "angulo_cat", "mecanismo_cat", "gancho",
              "angulo_desc", "mecanismo_desc", "prova", "oferta_cta", "alerta_compliance", "observacoes", "serve",
              "prova_cat", "modelar"]
    linhas = normalizar(aba.get("linhas", []), chaves)
    for i, ln in enumerate(linhas, 1):
        r = 4 + i
        texto(ws, f"A{r}", ln.get("#", i))
        texto(ws, f"B{r}", ln.get("marca"))
        texto(ws, f"C{r}", ln.get("titulo"))
        texto(ws, f"D{r}", link_da(ln, "Amostra", i))
        if ln.get("inicio"):
            formula(ws, f"E{r}", "=" + f_date(ln["inicio"]), nf="dd/mm/yyyy")
            formula(ws, f"F{r}", f"=$C$2-E{r}", nf="0")
        else:
            avisos.append(f"Amostra: linha {i} sem data de início")
        for col, k in zip("GHIJKLMNOPQRS", chaves[4:]):
            texto(ws, f"{col}{r}", ln.get(k), fill=F_AMARELO if col in "KLS" else None)
    cats = {k: categorias(aba, k, linhas, f"{k}_cat") for k in ["formato", "angulo", "mecanismo", "prova"]}
    for col, k in zip("GHIR", ["formato", "angulo", "mecanismo", "prova"]):
        dropdown(ws, col, cats[k])

    # quadro "Concorrentes diretos" (U4:AA9), alinhado ao cabeçalho de dados
    conc = normalizar(aba.get("concorrentes", []), ["marca", "produto", "preco", "mecanismo", "por_que", "page_id"])
    if not conc:
        avisos.append(f"{AMOSTRA}: quadro 'Concorrentes diretos' vazio")
    if len(conc) > MAX_CONCORRENTES:
        avisos.append(f"{AMOSTRA}: {len(conc)} concorrentes (máximo {MAX_CONCORRENTES}); só os 5 primeiros entram")
        conc = conc[:MAX_CONCORRENTES]
    texto(ws, "U1", "Concorrentes diretos", fonte=FONTE_NEG, al=None)
    texto(ws, "U2", "Anúncios já classificados", fonte=FONTE_NEG, al=None)
    formula(ws, "V2", f"=COUNTA($G$5:$G${FIM})", fonte=FONTE_NEG, al=None)
    cabecalho(ws, 4, column_index_from_string("U"),
              ["Marca", "Produto anunciado", "Preço visto", "Mecanismo/ingrediente", "Por que é concorrente direto",
               "Página na Biblioteca", "Anúncios ativos na dor"])
    marcas_linhas = {ln.get("marca") for ln in linhas}
    for k in range(MAX_CONCORRENTES):
        r = 5 + k
        if k < len(conc):
            c = conc[k]
            for col, ch in zip("UVWXY", ["marca", "produto", "preco", "mecanismo", "por_que"]):
                texto(ws, f"{col}{r}", c.get(ch))
            texto(ws, f"Z{r}", link_pagina(spec, c))
            if not c.get("por_que"):
                avisos.append(f"{AMOSTRA}: concorrente {c.get('marca')!r} sem 'por que é concorrente direto'")
            if c.get("marca") not in marcas_linhas:
                avisos.append(f"{AMOSTRA}: concorrente {c.get('marca')!r} sem nenhum anúncio na tabela")
        formula(ws, f"AA{r}", f'=IF(U{r}="","",COUNTIF($B$5:$B${FIM},U{r}))')

    # contadores (U:W) abaixo do quadro: marca, formato, ângulo, mecanismo, prova
    marcas = [c.get("marca") for c in conc if c.get("marca")]
    for ln in linhas:
        m = ln.get("marca")
        if m and m not in marcas:
            avisos.append(f"{AMOSTRA}: marca {m!r} na tabela não está no quadro 'Concorrentes diretos'; acrescentada")
            marcas.append(m)
    texto(ws, "U11", "Padrões da amostra", fonte=FONTE_NEG, al=None)
    lin = 12
    for rot, ops, col in [("Marca", marcas, "B"), ("Formato", cats["formato"], "G"), ("Ângulo", cats["angulo"], "H"),
                          ("Mecanismo", cats["mecanismo"], "I"), ("Prova", cats["prova"], "R")]:
        lin = bloco_contador(ws, lin, "UVW", rot, "% dos classificados", ops, col, "$V$2")
    larguras(ws, {"A": 5.1, "B": 27.6, "E": 12.0, "G": 27.6, "Q": 30.1, "R": 27.6, "S": 47.6, "T": 3.9,
                  "U": 30.1, "V": 27.6, "W": 13.9, "X": 27.6, "Y": 47.6, "Z": 30.1, "AA": 13.9})
    ws.freeze_panes = "A5"
    celulas_avulsas(ws, aba)


def aba_padroes(wb, spec, aba):
    ws = wb.create_sheet("B-E Padrões do nicho")
    titulo(ws, aba, "B. Ângulos · C. Formatos · D. Ganchos · E. Mecanismos do nicho de "
                    f"{spec.get('nicho', '')} ({spec.get('pais', '')}). Mínimo 60 caracteres por item "
                    "(ganchos sem mínimo).", LEGENDA)
    cabecalho(ws, 4, 1, ["Campo", "Item", "Padrão observado (matéria-prima)", "Evidência / fonte", "Sua versão",
                         "Caracteres da sua versão (mín. 60; ganchos sem mínimo)", f"Serve para {spec['_prod_art']}?"])
    chaves = ["secao", "item", "padrao", "evidencia", "sua_versao", "serve"]
    for i, ln in enumerate(normalizar(aba.get("linhas", []), chaves), 1):
        r = 4 + i
        sec = str(ln.get("secao", ""))
        texto(ws, f"A{r}", SECOES_PADROES.get(sec.upper()[:1], sec) if len(sec) <= 1 else sec)
        texto(ws, f"B{r}", ln.get("item"))
        texto(ws, f"C{r}", ln.get("padrao"))
        texto(ws, f"D{r}", ln.get("evidencia"))
        texto(ws, f"E{r}", ln.get("sua_versao"), fill=F_AMARELO)
        formula(ws, f"F{r}", f"=LEN(E{r})")
        texto(ws, f"G{r}", ln.get("serve"))
    larguras(ws, {"A": 12.6, "C": 27.6, "F": 15.1, "G": 30.1})
    ws.freeze_panes = "A5"
    celulas_avulsas(ws, aba)


def aba_big_ideas(wb, spec, aba):
    ws = wb.create_sheet("F - Big ideas + lacuna")
    titulo(ws, aba, "F. Big ideas (mín. 60 cada) + o que ninguém neste nicho está fazendo e você faria "
                    "(mín. 300).", LEGENDA)
    cabecalho(ws, 4, 1, ["Item", "Pista da pesquisa (não é a resposta)", "Evidência", "Cuidado de compliance",
                         "Sua versão", "Caracteres da sua versão (big idea mín. 60; lacuna mín. 300)"])
    chaves = ["item", "pista", "evidencia", "compliance", "sua_versao"]
    for i, ln in enumerate(normalizar(aba.get("linhas", []), chaves), 1):
        r = 4 + i
        for col, k in zip("ABCD", chaves[:4]):
            texto(ws, f"{col}{r}", ln.get(k))
        texto(ws, f"E{r}", ln.get("sua_versao"), fill=F_AMARELO)
        formula(ws, f"F{r}", f"=LEN(E{r})")
    larguras(ws, {"A": 27.6, "F": 15.1})
    ws.freeze_panes = "A5"
    celulas_avulsas(ws, aba)


def aba_voz(wb, spec, aba):
    ws = wb.create_sheet("Voz do cliente")
    idioma = f"em {spec['idioma']}" if spec.get("idioma") else "no idioma original"
    titulo(ws, aba, f"Frases reais do público (verbatim, {idioma}). Use para ganchos e para provar as "
                    "lacunas.", LEGENDA)
    cabecalho(ws, 4, 1, ["Frase", "Tema", "Fonte", "Sobre (marca ou genérico)"])
    chaves = ["frase", "tema", "fonte", "sobre"]
    for i, ln in enumerate(normalizar(aba.get("linhas", []), chaves), 1):
        r = 4 + i
        if ln.get("separador"):
            texto(ws, f"A{r}", ln["separador"])
            continue
        for col, k in zip("ABCD", chaves):
            texto(ws, f"{col}{r}", ln.get(k))
        if not ln.get("fonte") or not ln.get("sobre"):
            avisos.append(f"Voz do cliente: linha {i} sem fonte ou sem 'Sobre' (Marca/Genérico)")
    larguras(ws, {"A": 47.6})
    ws.freeze_panes = "A5"
    celulas_avulsas(ws, aba)


def aba_ia(wb, spec, aba):
    ws = wb.create_sheet("IA e o que travou")
    titulo(ws, aba, "Declaração de IA + 'O que travou e como resolveu' (mín. 150). Fatos reais desta pesquisa "
                    "para você redigir:", LEGENDA)
    cabecalho(ws, 4, 1, ["Fato", "Como foi resolvido"])
    for i, ln in enumerate(normalizar(aba.get("linhas", []), ["fato", "como_resolvido"]), 1):
        texto(ws, f"A{4 + i}", ln.get("fato"))
        texto(ws, f"B{4 + i}", ln.get("como_resolvido"))
    larguras(ws, {"A": 52.6})
    ws.freeze_panes = "A5"
    celulas_avulsas(ws, aba)


def aba_fontes(wb, spec, aba):
    ws = wb.create_sheet("Fontes")
    titulo(ws, aba, f"Fontes consultadas ({iso(spec['data_consulta']):%d/%m/%Y})", LEGENDA)
    cabecalho(ws, 4, 1, ["Fonte", "URL"])
    for i, ln in enumerate(normalizar(aba.get("linhas", []), ["fonte", "url"]), 1):
        texto(ws, f"A{4 + i}", ln.get("fonte"))
        texto(ws, f"B{4 + i}", ln.get("url"))
    larguras(ws, {"A": 52.6, "B": 65.1})
    ws.freeze_panes = "A5"
    celulas_avulsas(ws, aba)


ABAS = [("produto", aba_produto), ("referencias", aba_referencias), ("transcricoes", aba_transcricoes),
        ("candidatos", aba_candidatos), ("amostra", aba_amostra), ("padroes", aba_padroes),
        ("big_ideas", aba_big_ideas), ("voz_cliente", aba_voz), ("ia_travou", aba_ia), ("fontes", aba_fontes)]


def verificar_palavras(wb):
    for ws in wb.worksheets:
        for row in ws.iter_rows():
            for c in row:
                if isinstance(c.value, str) and not c.value.startswith("="):
                    t = sem_acento(c.value)
                    for p in PROIBIDAS:
                        if re.search(r"\b" + p + r"\b", t):
                            avisos.append(f"{ws.title}!{c.coordinate}: palavra proibida '{p}'")


def montar(spec, saida):
    spec.setdefault("_prod_art", spec.get("produto_com_artigo") or f"o {spec['produto']}")
    spec.setdefault("_marca_art", spec.get("marca_com_artigo") or f"a {spec.get('marca', '')}".strip())
    wb = Workbook()
    wb.remove(wb.active)
    abas = spec.get("abas", {})
    for chave, fn in ABAS:
        nomes = AMOSTRA_SINONIMOS if chave == "amostra" else [chave]
        fn(wb, spec, next((abas[n] for n in nomes if n in abas), {}))
    verificar_palavras(wb)
    wb.save(saida)
    return wb


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if len(args) != 2:
        sys.exit(__doc__.split("Formato do JSON")[0])
    with open(args[0], encoding="utf-8") as f:
        montar(json.load(f), args[1])
    for a in avisos:
        print("AVISO:", a)
    print("ok:", args[1])
    if avisos and "--estrito" in sys.argv:
        sys.exit(1)
