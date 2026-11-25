# Esquema da planilha (padrão do Oséias)

Gabarito: `gabarito/Pesquisa dark spots (Lumi) - EUA.xlsx` (dump célula a célula em `gabarito/lumi_dump.txt`).
O que está entre `[ ]` é o que muda por produto; o resto é literal. O script `scripts/montar_planilha.py`
já aplica tudo isto: o JSON leva só o conteúdo.

- `[produto]` = nome curto com artigo, ex.: "o Lumi" → `Serve para o Lumi?`
- `[marca]` = marca do produto com artigo, ex.: "a Farmasi" → `Alerta de compliance para a Farmasi`
- `[ângulo]`, `[nicho]`, `[país]`, `[data]` = ângulo/dor ("dark spots"), nicho em palavras ("manchas"), país da Biblioteca ("EUA"), data da consulta

**Nome do arquivo:** `Pesquisa [ângulo] ([produto]) - [país]`. Ex.: `Pesquisa dark spots (Lumi) - EUA`.

## Formato geral (todas as abas)

| Item | Regra |
|---|---|
| Linha 1 | Título da aba (A1). Negrito 11 só em *Produto* e *Transcrições*; nas outras, texto normal |
| Linha 2 | Legenda (A2). Padrão: `Legenda: células amarelas = você preenche, com suas palavras. O resto é matéria-prima com fonte.` (exceções na aba) |
| Linha 3 | Vazia, exceto em *Candidatos* (data da consulta) |
| Linha 4 | Cabeçalho: fundo `1E3863`, texto branco, negrito, Arial 10, quebra de texto, alinhado no topo |
| Linha 5+ | Dados: Arial 10, quebra de texto, alinhado no topo |
| Amarelo `FFF2CC` | Colunas que o Oséias preenche com as palavras dele. Pintar em **todas as linhas de dados** da coluna. Em geral ficam **vazias** (a IA não escreve o raciocínio dele) |
| Links | Célula que é só uma URL vira hyperlink, fonte azul `0000FF` |
| Datas | Sempre fórmula `DATE(a,m,d)`, formato `dd/mm/yyyy`; dias = data da consulta − `DATE(...)`, formato `0` |
| Percentuais | `IF(total=0,0,n/total)`, formato `0%` |
| Freeze | `A5` em todas (linhas 1–4 fixas), **exceto Transcrições: `D5`** (linhas 1–4 + colunas A–C) |
| Dropdowns | Validação de lista nas linhas 5–200 da coluna |
| Contagens | Intervalos `$X$5:$X$1000` |

## As 10 abas, nesta ordem

### 1. `Produto [nome do produto]`  (ex.: `Produto Lumi Radiance`)
- A1 (negrito 11): `Produto anunciado no ângulo [ângulo]: [nome oficial completo] ([observação, ex.: data da escolha])`
- A2: `O que está aqui é o texto oficial da [marca]. Só use no anúncio o que está nesta aba.`
- Linha 4: **A** `Campo` · **B** `Informação` · **C** `Fonte`
- Linhas de pares Campo/Informação/Fonte, nesta sequência no gabarito: Código · Preço ([país]) · Loja de afiliado · Promessa oficial (verbatim entre aspas) · Prova oficial (verbatim + asterisco/condição) · Como usar · Selos · Ingredientes (INCI) · Linha · Atenção (divergências de terceiros, ex.: Amazon com ingrediente que não está na página oficial).
- Depois de 1 linha vazia, seção em **negrito** em A: `O que muda na pesquisa`, com as linhas `Continua valendo` · `Sai` · `Muda` · `Novo trunfo` (Fonte = aba/coluna que sustenta, ex.: `Aba Amostra, coluna Q`).
- Depois de 1 linha vazia, seção em **negrito**: `Pendências de pesquisa`, linhas numeradas 1, 2, 3… em A e a pendência em B.
- Larguras: A 21,4 · B 70,1 · C 47,6. Freeze A5.

### 2. `A - Anúncios de referência`  (mínimo 10 linhas)
- A1: `A. Anúncios de referência para o ângulo [ângulo] (Biblioteca de Anúncios, [país], consulta em [dd/mm/aaaa]). Mínimo de 10 anúncios, com dados categorizados nas colunas M a R e contagem a partir da coluna T. Mínimos de texto: gancho 20 · ângulo 30 · mecanismo 30 · por que funciona 200 caracteres.`
- A2: legenda padrão. **M2** `Data da consulta` · **N2** `=DATE(aaaa,m,d)` (dd/mm/yyyy).

| Col | Cabeçalho (literal) | Conteúdo |
|---|---|---|
| A | `#` | 1, 2, 3… |
| B | `Link (Biblioteca)` | `https://www.facebook.com/ads/library/?id=[ID]` |
| C | `Marca` | marca (produto/criadora entre parênteses) |
| D | `Formato (assistir e escolher)` | descrição do criativo; dizer se foi assistido |
| E | `Tempo rodando` | texto: `Desde dd/mm/aaaa (~N dias)` (+ observação se abaixo do corte) |
| F | `Gancho transcrito (assistir)` | 1ª frase/fala entre aspas (mín. 20) |
| G | `Ângulo (proposta pelo texto; confirmar assistindo)` | mín. 30 |
| H | `Mecanismo (confirmar assistindo)` | `- Mecanismo do problema: … ⏎ - Mecanismo da solução: …` (mín. 30) |
| I | `Por que você acha que funciona (mín. 200): SEU raciocínio` | **AMARELA, vazia** |
| J | `Evidência de continuidade` | `TEMPO: ~N dias. VARIAÇÕES: …` com IDs |
| K | `Caracteres: gancho (mín. 20)` | `=LEN(F5)` |
| L | `Caracteres: por que funciona (mín. 200)` | `=LEN(I5)` |
| M | `Dias ativos` | `=$N$2-DATE(aaaa,m,d)` (data de início; formato `0`) |
| N | `Formato (categoria)` | dropdown |
| O | `Ângulo (categoria)` | dropdown |
| P | `Prova (categoria)` | dropdown |
| Q | `Oferta (categoria)` | dropdown |
| R | `Serve para [produto]?` | dropdown `Sim,Adaptar,Não` |

**Listas dos dropdowns** (as de N–Q são do nicho: monte com as categorias da amostra; as do gabarito servem de base):
- N Formato: `Estático de produto, Depoimento em vários dias, UGC (vários vídeos, mesmo texto), Talking head de especialista, Estático com depoimento, UGC de cliente, Vídeo da marca, UGC de criadora`
- O Ângulo: `Nomear pelo problema, Hábito / rotina simples, Já tentei de tudo, Autoridade, Antes e depois / rapidez, Público específico, Pergunta direta, Relato de clientes, Manchas no corpo`
- P Prova: `Popularidade (viral, nº 1, Amazon), Depoimento, Concentração / ingredientes, Autoridade médica, Antes e depois, Nenhuma, Garantia`
- Q Oferta: `Desconto / promoção, Nenhuma visível, Compre 1 leve 2, Garantia / devolução, Brinde, Comentar para receber link`
- R: `Sim, Adaptar, Não` (fixa)

**Contadores à direita (S vazia, larg. 3,9):**
- T1 `Dados das referências` (negrito)
- T2 `Referências` → U2 `=COUNTA($A$5:$A$1000)`
- T3 `Média de dias ativos` → U3 `=AVERAGE($M$5:$M$1000)` (formato `0`)
- T4 `Mediana de dias ativos` → U4 `=MEDIAN($M$5:$M$1000)` (formato `0`)
- T5 `Referências com mais de 100 dias` → U5 `=COUNTIF($M$5:$M$1000,">100")`  (T2–T5 em negrito)
- A partir de **T7**, um bloco por categoria, separados por 1 linha vazia: cabeçalho azul `[Formato | Ângulo | Prova | Oferta | Serve para [produto]?]` · `Anúncios` · `% das referências`; depois uma linha por opção da lista: T = opção, U `=COUNTIF($N$5:$N$1000,T8)` (coluna N/O/P/Q/R conforme o bloco), V `=IF($U$2=0,0,U8/$U$2)` (formato `0%`). No gabarito: Formato T7, Ângulo T17, Prova T28, Oferta T37, Serve T45.
- Larguras: A 5,1 · B 27,6 · K 13,9 · M 10,1 · N 21,4 · S 3,9 · T 30,1 · U 13,9. Freeze A5.

### 3. `Transcrições`  (1 linha por vídeo de referência)
- A1 (negrito 11): `Transcrições dos vídeos de referência: um anúncio por linha, desmontado em gancho, body, ângulo, CTA e o que modelar para [produto].`
- A2: como a transcrição foi feita (ex.: `Transcrição feita pelas legendas queimadas no vídeo, quadro a quadro. O áudio não foi transcrito: confira a fala se o vídeo não tiver legenda.`)
- Linha 4: **A** `#` · **B** `Link (Biblioteca)` · **C** `Marca / quem fala` · **D** `Vídeo no Drive` · **E** `Duração` · **F** `Formato` · **G** `Gancho visual (0 a 3 s)` · **H** `Gancho falado` · **I** `Texto fixo na tela` · **J** `Body (transcrição completa)` · **K** `Estrutura (tempo → bloco → função)` · **L** `Ângulo` · **M** `Mecanismo` · **N** `Prova` · **O** `CTA falado` · **P** `CTA da copy / botão` · **Q** `Destino` · **R** `Copy do anúncio` · **S** `O que modelar para [produto]` (**AMARELA**, preenchida como matéria-prima) · **T** `Não transportar` · **U** `Cobertura`
- D: link do vídeo na pasta `Referências (vídeos)` ou `Pendente: subir [nn]_[marca]_[criador]_[tema]_[ID].mp4 na pasta 'Referências (vídeos)'`.
- K: um bloco por linha `0-4 s → [o que acontece] → [função]`, separados por ` ⏎ `.
- U: o que foi visto/ouvido (ex.: `Vídeo inteiro quadro a quadro (2,5 por segundo) + legendas lidas; áudio não transcrito`).
- Larguras: A 4,5 · B 27,6 · E 8,9 · F 27,6 · J 47,6 · L 27,6. **Freeze D5.**

### 4. `Candidatos (Biblioteca)`  (ativos há mais de 100 dias)
- A1: `Somente anúncios ATIVOS há MAIS DE 100 DIAS sobre [nicho] (Biblioteca de Anúncios, [país]). [como as datas foram lidas/conferidas]`
- A2: resumo de quem passou do corte + limitações da coleta (ex.: limite de 50 anúncios por busca do conector).
- **A3** `Data da consulta` · **B3** `=DATE(aaaa,m,d)` (dd/mm/yyyy).
- Linha 4: **A** `Anunciante` · **B** `Título do anúncio (ou 1ª linha quando não há título)` · **C** `Link` · **D** `Data de início` (`=DATE(aaaa,m,d)`, dd/mm/yyyy) · **E** `Tempo no ar (dias)` (`=$B$3-D5`, formato `0`) · **F** `Observação` · **G** `Serve para [produto]?` (texto livre: `Sim`/`Adaptar: …`/`Não: …`/`Lacuna N (…)`)
- Sem coluna `#` e sem coluna de ID (o ID está no link). Larguras: A 27,6 · D 13,9 · F 27,6. Freeze A5.

### 5. `Amostra concorrentes`  (todos os anúncios ativos na dor de até 5 concorrentes diretos)
Antigo `Amostra 3 marcas` (3 marcas por volume de anúncios). O script aceita a chave antiga (`amostra_3_marcas`) e JSON sem o quadro nem as colunas novas; o gabarito ainda tem o nome antigo e 3 marcas.
- A1: `Amostra dos concorrentes diretos: todos os anúncios ativos sobre [nicho] de até 5 concorrentes (Biblioteca de Anúncios Meta, [país]). [recorte de cada marca]`
- **A2** `Data da consulta` · **C2** `=DATE(aaaa,m,d)` · **E2** `Colunas G, H, I e R têm lista suspensa para contar os padrões no quadro ao lado (coluna U em diante).`
- Linha 4: **A** `#` · **B** `Marca` · **C** `Título na Biblioteca` · **D** `Link` · **E** `Ativo desde` (`=DATE(...)`) · **F** `Dias ativos` (`=$C$2-E5`, `0`) · **G** `Formato (categoria)` · **H** `Ângulo (categoria)` · **I** `Mecanismo (categoria)` · **J** `Gancho transcrito (1ª frase do texto)` · **K** `Ângulo (descrição)` (**AMARELA, vazia**) · **L** `Mecanismo (descrição)` (**AMARELA, vazia**) · **M** `Prova / autoridade usada` · **N** `Oferta / CTA` · **O** `Alerta de compliance para [marca]` · **P** `Observações` · **Q** `Serve para [produto]?` (texto livre) · **R** `Prova (categoria)` · **S** `O que modelar deste concorrente` (**AMARELA, vazia**: o Oséias escreve)
- A–Q como no gabarito; R e S foram acrescentadas no fim para não mexer nas colunas que ele já conhece. **B (Marca) usa exatamente o nome do quadro** (é o que o `COUNTIF` conta).
- Dropdowns (do nicho; base do gabarito):
  - G: `UGC de criadora (parceria), UGC (vários vídeos, mesmo texto), Vídeo da marca, Estático de produto, Estático com rosto/montagem`
  - H: `Nomear pelo problema, Manchas no corpo, Marcas de acne, Já tentei de tudo, Idade / reflexo (50+), Simplicidade / constância, Olheiras e linhas, Sol acumulado, Recomendação de creator`
  - I: `Vitamina C (não explicado), Vitamina C + glutationa/niacinamida, Ácido tranexâmico + niacinamida, Óleos botânicos, Não explicado`
  - R: `Popularidade (viral, nº 1, Amazon), Depoimento / uso pessoal, Concentração / ingredientes, Demonstração / tutorial, Celebridade, Nenhuma` (base; acrescente as do nicho)
- T vazia (larg. 3,9). **U1** `Concorrentes diretos` (negrito) · **U2** `Anúncios já classificados` / **V2** `=COUNTA($G$5:$G$1000)` (negrito).
- **Quadro `Concorrentes diretos` (U4:AA9)**, cabeçalho azul na linha 4 (alinhado ao cabeçalho dos dados), 5 linhas reservadas (5–9), uma por concorrente, na ordem de entrada:

| Col | Cabeçalho (literal) | Conteúdo |
|---|---|---|
| U | `Marca` | nome igual ao da coluna B |
| V | `Produto anunciado` | o produto que ela anuncia na dor |
| W | `Preço visto` | preço com moeda e onde foi visto, ou `n/v` |
| X | `Mecanismo/ingrediente` | ativo/mecanismo que o anúncio ou a página nomeia |
| Y | `Por que é concorrente direto` | semelhança de produto · mecanismo · preço · dor, e presença na Meta (nº de ativos na dor) |
| Z | `Página na Biblioteca` | `https://www.facebook.com/ads/library/?active_status=active&ad_type=all&country=[código]&view_all_page_id=[page_id]&search_type=page&media_type=all` (hyperlink) |
| AA | `Anúncios ativos na dor` | `=IF(U5="","",COUNTIF($B$5:$B$1000,U5))` (em todas as 5 linhas) |

- **Contadores (U:W) abaixo do quadro:** U11 `Padrões da amostra` (negrito). Blocos a partir de **U12**, separados por 1 linha vazia: cabeçalho azul `[Marca | Formato | Ângulo | Mecanismo | Prova]` · `Anúncios` · `% dos classificados`; linhas: V `=COUNTIF($B$5:$B$1000,U13)` (B/G/H/I/R conforme o bloco), W `=IF($V$2=0,0,V13/$V$2)` (`0%`). O bloco Marca lista os concorrentes do quadro.
- Larguras: A 5,1 · B 27,6 · E 12 · G 27,6 · Q 30,1 · R 27,6 · S 47,6 · T 3,9 · U 30,1 · V 27,6 · W 13,9 · X 27,6 · Y 47,6 · Z 30,1 · AA 13,9. Freeze A5.

### 6. `B-E Padrões do nicho`
- A1: `B. Ângulos · C. Formatos · D. Ganchos · E. Mecanismos do nicho de [nicho] ([país]). Mínimo 60 caracteres por item (ganchos sem mínimo).`
- A2: legenda padrão.
- Linha 4: **A** `Campo` · **B** `Item` · **C** `Padrão observado (matéria-prima)` · **D** `Evidência / fonte` · **E** `Sua versão` (**AMARELA, vazia**) · **F** `Caracteres da sua versão (mín. 60; ganchos sem mínimo)` (`=LEN(E5)`) · **G** `Serve para [produto]?` (texto livre)
- A (Campo) usa exatamente: `B. Ângulo`, `C. Formato`, `D. Gancho`, `E. Mecanismo`, nesta ordem de blocos. B (Item) = 1, 2, 3… e `extra` para o item além da conta. Em `D. Gancho`, C é o gancho verbatim entre aspas. D = marca + ID + trecho.
- Larguras: A 12,6 · C 27,6 · F 15,1 · G 30,1. Freeze A5.

### 7. `F - Big ideas + lacuna`
- A1: `F. Big ideas (mín. 60 cada) + o que ninguém neste nicho está fazendo e você faria (mín. 300).`
- A2: legenda padrão.
- Linha 4: **A** `Item` · **B** `Pista da pesquisa (não é a resposta)` · **C** `Evidência` · **D** `Cuidado de compliance` · **E** `Sua versão` (**AMARELA, vazia**) · **F** `Caracteres da sua versão (big idea mín. 60; lacuna mín. 300)` (`=LEN(E5)`)
- Itens (A), nesta ordem: `Lacuna 1` … `Lacuna 5` · `Diferenciação` · `Big idea (pista)`. Lacuna = "não encontrado na amostra" + o que o produto tem para ocupar.
- Larguras: A 27,6 · F 15,1. Freeze A5.

### 8. `Voz do cliente`
- A1: `Frases reais do público (verbatim, em [idioma]). Use para ganchos e para provar as lacunas.`
- A2: legenda padrão.
- Linha 4: **A** `Frase` · **B** `Tema` · **C** `Fonte` · **D** `Sobre (marca ou genérico)`
- C = URL da fonte (pode ter observação depois: `… (comentário, vídeo X)`); D = `Genérico` ou `Marca [marca]`.
- Separador de coleta numa linha só em A: `--- Coleta aaaa-mm-dd: [fontes] ---`.
- Última linha = resumo: A com notas agregadas (ex.: `Trustpilot …: nota 3,1/5 em 46 avaliações…`) e limitações (fonte bloqueada etc.), B `Resumo e limitações`.
- Larguras: A 47,6. Freeze A5.

### 9. `IA e o que travou`
- A1: `Declaração de IA + 'O que travou e como resolveu' (mín. 150). Fatos reais desta pesquisa para você redigir:`
- A2: legenda padrão.
- Linha 4: **A** `Fato` · **B** `Como foi resolvido`. Um fato por linha (o que travou, limite de ferramenta, decisão de amostra, divergência de fonte).
- Larguras: A 52,6. Freeze A5.

### 10. `Fontes`
- A1: `Fontes consultadas ([datas])`
- A2: legenda padrão.
- Linha 4: **A** `Fonte` · **B** `URL`. Busca na Biblioteca = URL da busca/página com filtros; conector sem URL = `Conector Meta no Claude (sem URL)`.
- Larguras: A 52,6 · B 65,1. Freeze A5.

## Regras técnicas

- **IDs da Meta sempre texto.** No .xlsx: célula string com formato `@` (o script faz). No Google Sheets via API: gravar `'` + ID. Nunca número: acima de 15 dígitos o Sheets mostra `2,54937E+15` e perde dígitos (IDs de 17 dígitos não cabem num número). No JSON, ID vai como string.
- **Texto que começa com `=`, `+`, `-`, `@`** (ex.: `- Mecanismo do problema`, `+50%`, `@criadora`): é texto, não fórmula. No .xlsx o script grava como string com *quotePrefix* (o apóstrofo invisível). No Sheets via API (`USER_ENTERED`): prefixar com `'`. Texto que começa com `'` (citação, ex.: `'Miracle in a bottle'`) também ganha um `'` extra no Sheets, senão o primeiro apóstrofo some.
- **Separador de fórmula:** .xlsx (openpyxl) usa `,` → `=DATE(2026,11,24)`, `=COUNTIF($R$5:$R$1000,T46)`. Ao importar o .xlsx o Sheets converte sozinho. Escrevendo direto no Google Sheets com locale pt-BR: `;` → `=DATE(2026;11;24)`, `=IF($U$2=0;0;U8/$U$2)`.
- Datas e dias sempre por fórmula (`DATE`, data da consulta − início). Nunca digitar o número de dias.
- Dado não visível = `n/v`.

---

## Apêndice — Swipe do Oséias (aba `Índice`)

Gabarito: `gabarito/Swipe - Indice.xlsx` (dump em `gabarito/indice_dump.txt`). Só entra referência que **ele aprovar**.
Use `scripts/adicionar_ao_swipe.py` (acrescenta no fim, pula ID repetido, e com `--reparar-ids` corrige os IDs numéricos usando o link).

- Uma aba só: `Índice`. **Cabeçalho na linha 1** (fundo `EDEDED`, negrito, texto preto), dados a partir da linha 2. **Freeze E2** (linha 1 + colunas A–D).
- Colunas (literal):

| Col | Cabeçalho | Conteúdo |
|---|---|---|
| A | `#` | sequencial (último + 1) |
| B | `Adicionado em` | `aaaa-mm-dd` (texto) |
| C | `Nicho` | ex.: `Skincare - vitamina C (manchas)` |
| D | `Marca / produto` | |
| E | `Página que anuncia` | ex.: `Sara Hesri com Arencia Global (criadora)` |
| F | `País da busca` | ex.: `EUA` |
| G | `Início` | `aaaa-mm-dd` (texto; é o que a fórmula de H lê) |
| H | `Dias no ar` | `=IF(G2="","",TODAY()-DATEVALUE(G2))` (formato `0`; já vem pré-preenchida até a linha 500 — **não** sobrescrever com número) |
| I | `Status (última checagem)` | `Ativo (dd/mm/aaaa)` [+ observação, ex.: `, baixo volume de impressões (<100)`]; orgânico: `Orgânico, sem data` |
| J | `Formato` | |
| K | `Gancho verbal` | verbatim; título depois de ` \| Título: ` |
| L | `Gancho visual` | ou `Não visto` |
| M | `Estrutura (sequência)` | blocos separados por ` → ` |
| N | `Ângulo / desejo / objeção` | |
| O | `Avatar` | |
| P | `Prova` | |
| Q | `Oferta e CTA` | itens separados por ` · ` |
| R | `Destino` | domínio |
| S | `O que aprender` | |
| T | `Não transportar sem prova` | |
| U | `Como foi visto` | ex.: `Texto + miniatura (vídeo não baixado)` |
| V | `Link Ad Library` | `https://www.facebook.com/ads/library/?id=[ID]` |
| W | `ID` | **texto** (formato `@`) |
| X | `Mídia no Drive` | link da pasta/arquivo, se houver |
| Y | `Tags` | separadas por `; ` |

- Larguras: A 5,1 · B 15,1 · D 22,6 · E 15,1 · J 32,6 · V 20,1.
- Problemas no Índice atual (não repetir): IDs da coluna W como número nas linhas 2, 4, 5, 6, 9 e 11 (aparecem como `2,54937E+15` e podem perder dígitos); linhas 21–24 com H em número fixo no lugar da fórmula; B/G misturando data e texto.
