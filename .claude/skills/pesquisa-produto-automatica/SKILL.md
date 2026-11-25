---
name: pesquisa-produto-automatica
description: Pesquisa completa de anúncios para um produto (etapa 1) — Biblioteca de Anúncios da Meta, ≥10 referências, transcrições, voz do cliente, padrões, lacunas e big idea — entregue numa planilha no padrão do Oséias. Use quando ele trouxer um produto para pesquisar, pedir "pesquisa esse produto", "espiona o nicho de X" ou "vamos anunciar X".
---

# Pesquisa automática por produto (etapa 1)

Você é o **orquestrador**. Distribua o trabalho entre trabalhadores (panes no Overclock, subagentes fora dele), junte os resultados, monte a planilha e verifique. **Não escreva brief nem anúncio**: a pesquisa termina na planilha. Brief (etapa 2) e anúncio com 5–6 ganchos + 1 body (etapa 3) só quando o Oséias pedir.

<!-- Não escreva cifrão seguido de número neste arquivo: o carregador de skills troca esses trechos pelos argumentos da chamada. Fórmulas com referência absoluta ficam só em references/planilha.md. -->
Antes de começar, leia:
- `references/regras.md` — regras de conteúdo que todo subagente deve seguir (cole-as no prompt de cada um).
- `references/planilha.md` — esquema exato das 10 abas.
- `references/brief.md` — modelo do brief (etapa 2), só quando o Oséias pedir.

## Modo híbrido (Mac coleta, VPS processa)
Use quando o Oséias pedir "híbrido" ou quando você estiver na VPS (Hermes). A divisão existe porque a Meta, o Reddit, o TikTok e o YouTube bloqueiam IP de servidor.
- **Mac (Overclock, IP de casa): tudo que acessa os sites.**
  1. Faça os Passos 0 a 3 completos: produto, palavras-chave, Meta, concorrentes, Reddit, TikTok e o `coletar.py`.
  2. Rode o `classificador-referencias`.
  3. Baixe os 10–12 vídeos de `para_transcrever` **sem transcrever**: `python3 scripts/transcrever.py 'https://www.facebook.com/ads/library/?id=ID' --so-baixar --pasta pesquisas/[produto]/videos`. Renomeie cada arquivo para `NN_marca_tema_ID.mp4`.
  4. Grave `pesquisas/[produto]/etapa.json` com `{"etapa": "coleta_ok", "data": "AAAA-MM-DD", "pasta_drive": "<id>", "planilha_drive": "<id ou null>"}`.
  5. Envie com `sh scripts/sincronizar.sh enviar [produto]`, na raiz do repositório.
  6. Diga ao Oséias que a coleta foi enviada e qual pedido fazer ao Hermes: "processa a pesquisa [produto]".
- **VPS (Hermes): só arquivos locais, sem navegador.** Ao receber "processa a pesquisa [produto]":
  1. Confira em `etapa.json` que a etapa é `coleta_ok`.
  2. Transcreva cada mp4 de `videos/` pelo **arquivo** (Passo 4), um por vez.
  3. Siga os Passos 5 a 7 e suba no Drive. Use `--atualizar` se `planilha_drive` vier preenchido.
  4. Grave `etapa.json` com `"etapa": "entregue"` e o link da planilha.
  - Se faltar algum arquivo da coleta, **não** tente buscar na internet. Registre em *IA e o que travou* e peça ao Mac.
- O Mac pode trazer o resultado de volta com `sh scripts/sincronizar.sh receber [produto]`. Os dados da pesquisa nunca passam pelo Git.

## Passo 0 — Briefing
Precisa de: produto (nome exato), link oficial, país da Biblioteca (não presumir BR), idioma dos anúncios, ângulo/dor, modelo de venda (afiliado, DTC, infoproduto…), destino (pasta do Drive ou pasta local). Pergunte **só** o que faltar, numa mensagem. Com o mínimo, comece.

## Passo 1 — Checar ferramentas (silencioso)
| Ferramenta | Para quê | Se faltar |
|---|---|---|
| **Navegador logado** — no Overclock: `overclock_browser_act` (já logado em Facebook, Reddit e TikTok); fora dele: Claude in Chrome ou Playwright MCP | Biblioteca da Meta, Reddit, TikTok | Registre "varredura X não executada" em *IA e o que travou* e siga |
| `yt-dlp` + Python 3 (`openpyxl`) | Voz do cliente no YouTube; montar a planilha | — |
| `ffmpeg` + `whisper-cli` (whisper.cpp em `~/.local/bin`, modelo `~/.cache/whisper-cpp/ggml-small.bin`) | Baixar, transcrever e tirar frames dos vídeos: `python3 scripts/transcrever.py 'https://www.facebook.com/ads/library/?id=ID' --frames 16 --pasta pesquisas/[produto]/videos --saida pesquisas/[produto]/transcricoes/ID.json` (aceita arquivo, link da Meta ou URL do yt-dlp; ~75 s por minuto de áudio neste Mac) | O script devolve `fala_verificada: false`, "fala não verificada": transcrever pelas legendas queimadas do mosaico e declarar em *Cobertura* |
| Google Drive MCP + `gcloud` (logado com `gcloud auth login --enable-gdrive-access`, conta editora da pasta) | MCP: ler o swipe e pesquisas anteriores · `gcloud`: **subir** a planilha e os vídeos (`scripts/subir_drive.py`) | Sem token do gcloud: entregue o `.xlsx` local e diga ao Oséias como logar |

Pasta de trabalho da pesquisa: `pesquisas/[produto]/` (JSON intermediários, brutos e a planilha final). Todo trabalhador grava o resultado ali, não só no chat.

## Passo 2 — Disparar o trabalho em paralelo
**Como paralelizar:** no Overclock, cada linha abaixo vira um **pane** (`pane_spawn`, todos numa única chamada com `panes:[…]`); o pane devolve por `handoff_submit` com o caminho do JSON que gravou. Fora do Overclock: no Claude Code, use os subagentes de mesmo nome (`.claude/agents/`); no Codex, Gemini CLI e outros sem subagentes, rode cada trabalhador você mesmo, em sequência, lendo `.claude/agents/<nome>.md` como instrução (ver `AGENTS.md` na raiz). Os panes herdam o seu modelo; não fixe modelo. Cole `references/regras.md` no prompt de cada um.

**Limite de navegadores (testado 2026-11-25):** no máximo **2 navegadores abertos ao mesmo tempo** no total, e a Biblioteca da Meta em **um só navegador, em série**, com pausa de ≥5 s entre buscas. Quatro varredores em paralelo na mesma conta tomaram HTTP 403 da Meta em todas as buscas e travaram o navegador do Overclock inteiro (nem o Google abria). Nunca reabra navegador novo para "tentar de novo" depois de 403 ou timeout: pare, registre e devolva ao orquestrador. Ordem segura: 1 varredor-meta com todos os grupos de termos em sequência + 1 trabalhador de navegador para Reddit/TikTok; scripts (YouTube, comentários do TikTok) rodam em paralelo sem limite.

**Navegador:** cada trabalhador que navega abre o **próprio** navegador (`overclock_browser_act` com `paneId: "new"`) e reutiliza esse `paneId` até o fim; dois trabalhadores no mesmo navegador se atropelam. O texto lido por chamada é truncado (~10 mil caracteres): role (`scroll`) e leia de novo para paginar.

| Trabalhador | Quando | Entrada | Saída (em `pesquisas/[produto]/`) |
|---|---|---|---|
| `pesquisador-produto` | já | link oficial + produto | `produto.json` (aba Produto) |
| `varredor-meta` (**um só**, em série) | depois das palavras-chave (abaixo) | lista de termos em baldes, país, idioma, data de corte; no fim, as páginas dos concorrentes diretos (Passo 3) | `meta.json` (anúncios + protocolo, gravado após cada termo e cada página) |
| `coletor-voz-cliente` | já | produto, marca, dor, idioma, país | `voz-cliente/` → frases classificadas |
| coletor Reddit (navegador) | já | subreddits do nicho + termos da dor | `voz-cliente/brutos/reddit_navegador/reddit_navegador.jsonl` (≥40 comentários) |
| coletor TikTok (navegador) | já | termos da dor + produto | `voz-cliente/brutos/tiktok_navegador/videos.txt` (~15–30 URLs de vídeo) |

**Voz do cliente é por script:** `coletor-voz-cliente` roda `scripts/voz_cliente/coletar.py` — YouTube via yt-dlp (~1.800 comentários em ~3 min) + TikTok via `tiktok.py` (~1.150 comentários de 27 vídeos em ~1,5–2,5 min) + Reddit relido dos arquivos do navegador — e só classifica os candidatos (cota mínima por fonte = N/5). Rode-o **depois** dos coletores de navegador, ou de novo com `--so-filtrar --coletar-tiktok` (não refaz o YouTube; baixa o TikTok do `videos.txt` e relê o Reddit). Passe `--dor 'melasma; sun spots; …'` com sinônimos da dor: sem eles, relatos emocionais que não usam o termo exato caem como irrelevantes.

**Reddit pelo navegador** (API anônima, curl_cffi e criação de app estão bloqueados) — o navegador **lê**, o agente **grava**: busque **dentro** dos subreddits do nicho (nunca na busca geral), com termos de 1–2 palavras, e só navegue por URL (não vote, não entre, não comente).
1. Comentários direto: `https://www.reddit.com/r/SUB/search/?q=TERMO&type=comments&sort=top` → cada leitura traz ~6–9 comentários com texto, votos e o link (`elements` com href `/r/SUB/comments/POST/slug/CID/`). A leitura é truncada a partir do **topo** da página: rolar não pagina; troque de termo/subreddit.
2. Tópico inteiro (rende mais: ~25 comentários por leitura, com pontos): abra um tópico emocional achado no passo 1 em `https://old.reddit.com/r/SUB/comments/POST/slug/?sort=top&depth=1`. Só os 2–3 primeiros comentários trazem o `permalink` com CID nos `elements` (limite de 120); os demais ficam com o link do tópico.
3. Monte um lote JSON e grave com `python3 scripts/voz_cliente/reddit_navegador.py <pasta>/brutos/reddit_navegador/reddit_navegador.jsonl lote.json` — lote = `[{"subreddit":"…","termo":"…","titulo":"…","permalink":"/r/…/comments/ID/…/CID/","likes":372,"texto":"<verbatim>"}]` (contrato no topo de `reddit.py`). O script deduplica, converte "1.7K", cria id para link de tópico e não aceita autor. **Texto inteiro e verbatim** (aspas curvas, quebras de linha, erros de digitação); comentário cortado pela truncagem não entra. Guarde os lotes em `reddit_navegador/lotes/`.
4. Para objeção à marca: `r/antiMLM` com `q=[marca] skincare` e o tópico "What is the deal with [marca]" em old.reddit. Meta: ≥40 comentários de ≥4 subreddits (~20 leituras, ~15 min).

**TikTok: navegador descobre → script coleta.** A busca exige assinatura (só no navegador); os comentários saem por script sem login. (1) No navegador: `https://www.tiktok.com/search/video?q=TERMO`, role uma vez (`scroll` 1500) e leia: os `elements` trazem `https://www.tiktok.com/@user/video/ID`. **Não clique em nada** (índices mudam entre leituras; um clique errado já favoritou um vídeo na conta). (2) Grave as URLs em `<pasta>/brutos/tiktok_navegador/videos.txt`, uma por linha, com `# termo: TERMO` antes de cada grupo (opcional: `URL<TAB>legenda`). (3) `coletar.py` (ou `python3 scripts/voz_cliente/tiktok.py --videos …/videos.txt --saida …/brutos/tiktok.jsonl`) baixa até 150 comentários de 1º nível por vídeo via `curl_cffi` (`/api/comment/list/`, pausa de 1 s), com a legenda do vídeo como título; sem `curl_cffi` registra em `nao_consegui` e segue. A busca segue o país/idioma da conta logada (conta BR: termo de marca traz vídeos em espanhol/português) — prefira termos da dor em inglês; o filtro descarta outro idioma pelo `comment_language` do TikTok. **Plano B sem navegador** (navegador travado ou ocupado com a Meta): descubra os vídeos por WebSearch `site:tiktok.com TERMO` — as URLs `/@user/video/ID` dos resultados vão direto para o `videos.txt` (testado 2026-11-25: 17 vídeos, 464 comentários).

**Palavras-chave da Meta: pesquise antes de varrer (nunca só o termo amplo).** Um termo solto como "dark spots" traz shampoo, Groupon, clínica e app; a varredura só rende com termos específicos do produto e dos concorrentes. Ordem: (1) `pesquisador-produto` e a coleta de voz do cliente rodam **primeiro** (são scripts e não disputam o navegador); (2) você levanta as palavras-chave; (3) só então lança o `varredor-meta`.
Fontes das palavras-chave:
- **Produto** (`produto.json`): nome, categoria, ingredientes-chave e o mecanismo (ex.: uva-ursi → 'bearberry', 'alpha arbutin'), o número da prova (ex.: 'melanin', 'in 4 weeks').
- **Voz do cliente** (`voz-cliente/brutos/*.jsonl`): conte por código as marcas, os ingredientes e as palavras da dor mais citados nos comentários — viram o balde de concorrentes e o de dor na boca do cliente (piloto Lumi: Remedy, Eucerin/Thiamidol, Anua, Topicals Faded, The Ordinary; 'age spot', 'melasma', 'brown spot').
- **Mais vendidos da categoria**: WebSearch '[categoria] best seller Amazon [ano]' (piloto: Topicals Faded, Good Molecules, Murad, Caudalie, Garnier, La Roche-Posay).
- **Pesquisa anterior do mesmo nicho** no Drive/`gabarito/` (páginas que lideraram, termos que renderam).
Monte 20–30 termos em 5 baldes — categoria específica ('dark spot serum', não 'dark spots'), dor na boca do cliente, mecanismo/ingrediente, oferta/prova, **concorrentes pelo nome** — e marque com * os 6–8 principais. Todos os termos vão com `start_date[max]=` (data da consulta − 100 dias; testado: o filtro funciona e traz só longevos); os marcados com * também sem o filtro, para ver o que roda hoje. Relevância estrita na coleta: só o tipo de produto pesquisado; descartes contados no protocolo. Um único `varredor-meta`, em série (ver limite de navegadores). Para a voz do cliente, inclua termos de **objeção à marca** (ex.: "[marca] scam", "[marca] review") — é onde aparece o que o anúncio precisa responder.

## Passo 3 — Consolidar (você, com código)
1. Junte os JSON dos varredores; **deduplique por Library ID**.
2. Calcule dias desde o início **por código** (data da consulta − data de início).
3. **Candidatos** = ativos com > 100 dias (se vier < 15, baixe para > 60 e registre).
4. **Até 5 concorrentes diretos** → base da aba *Amostra concorrentes*. Concorrente direto = vende produto **semelhante** ao pesquisado para a **mesma dor**, com preço próximo, e anuncia na Meta agora. Critérios, nesta ordem:
   1. **Semelhança primeiro** (de `produto.json` × copy/destino dos anúncios coletados): mesmo tipo de produto (sérum × sérum, não clínica ou app), mesmo mecanismo/ingrediente ou mecanismo rival para a mesma dor, faixa de preço próxima (mesma ordem de grandeza; preço visto no anúncio ou na página de destino, senão `n/v`).
   2. **Presença na Meta depois**: anúncios ativos nessa dor no país da pesquisa (≥3 na coleta, ou página com muitos ativos). Volume sozinho não faz concorrente direto: marca grande com outro tipo de produto fica fora; marca pequena e idêntica entra.
   3. Fontes dos nomes: as páginas que aparecem em `meta.json`, o balde de concorrentes das palavras-chave e as marcas citadas na voz do cliente. Menos de 5 que passem nos critérios = entram menos (registre em *IA e o que travou*; não complete com marca que não é direta).
   Para cada um registre marca, produto anunciado, preço visto, mecanismo/ingrediente, **por que entrou** (qual critério bateu e qual não bateu) e o `page_id` da página (está no link da página do anúncio). Grave em `pesquisas/[produto]/concorrentes.json`.
5. **Varredura da página de cada concorrente** — pelo **mesmo `varredor-meta` único**, no **fim da lista de termos** (no Overclock, `pane_write` no pane dele, que reutiliza o navegador já aberto; fora dele, `SendMessage` ao mesmo subagente; nunca um segundo varredor, ver limite de navegadores). Para cada `page_id`: abra `https://www.facebook.com/ads/library/?active_status=active&ad_type=all&country=PAIS&view_all_page_id=PAGE_ID&search_type=page&media_type=all`, role até o fim (não só os 60 primeiros) e colete **todos os anúncios ativos da página nessa dor** (descarte os de outras dores/produtos e conte os descartes no protocolo), com `"concorrente_direto": true` e `"page_id"` em cada anúncio, gravados no mesmo `meta.json`. Anúncio que já veio pelas palavras-chave: deduplique pelo ID e mantenha `concorrente_direto: true`. Página com centenas de ativos: a meta continua sendo todos os da dor; se a rolagem travar antes do fim, registre o recorte (quantos vistos de quantos) no título da aba (A1) e em *IA e o que travou*.

## Passo 4 — Classificar e transcrever
- `classificador-referencias`: recebe candidatos + anúncios dos concorrentes diretos + `concorrentes.json` + aba Produto; devolve **no mínimo 10** referências classificadas, a classificação de **todos** os anúncios dos concorrentes diretos (`concorrente_direto: true`) e o quadro *Concorrentes diretos* preenchido a partir de `concorrentes.json`. Prioridade: relevância para o produto → dias → variações; reservar 1–2 recentes/diferentes.
- **Vídeos para baixar e transcrever: 10 a 12**, escolhidos pelo classificador entre os anúncios em vídeo (lista `para_transcrever`, com o motivo de cada um). Prioridade: os mais longevos e os dos concorrentes diretos; reservar 1–2 recentes ou diferentes. (Piloto Lumi com 8 vídeos: 6 sem fala e 2 de axila — mais vídeos dão margem para os que rendem pouco.)
- `transcritor`: 2 panes, cada um com metade da lista, **um vídeo por vez** (o whisper ocupa a CPU; ~1 min por vídeo neste Mac). Transcrição separada em gancho visual / falado / texto na tela / body / CTA, com cobertura declarada.

## Passo 5 — Síntese
`sintetizador` recebe tudo (produto, referências, transcrições, voz do cliente) e devolve as abas *B-E Padrões* e *F - Big ideas + lacuna*.

## Passo 6 — Montar a planilha
Siga `references/planilha.md` à risca (10 abas, cabeçalho na linha 4, colunas amarelas vazias para o Oséias). Nome: `Pesquisa [ângulo] ([produto]) - [país]`.
- **Monte o `.xlsx`** em `pesquisas/[produto]/`. Monte um JSON com o conteúdo (formato no topo do script) e rode:
  `python3 scripts/montar_planilha.py pesquisa.json "pesquisas/[produto]/Pesquisa [ângulo] ([produto]) - [país].xlsx" --estrito`
  O script já aplica cabeçalhos, cores, dropdowns, fórmulas (`LEN`, dias = data da consulta − `DATE(...)`, `COUNTA`/`AVERAGE`/`MEDIAN`/`COUNTIF`, `%`), blocos de contadores e freeze. Os avisos que ele imprime são pendências: corrija ou registre em *IA e o que travou*.
- **Entrega padrão: direto no Drive**, na pasta do produto (`Swipe de Anúncios/[Área]/Ads - [Marca]/Produtos/[Produto]/` — ache o ID com o Drive MCP, `search_files` com `parentId = '…'`; crie a pasta do produto se faltar): `python3 scripts/subir_drive.py --pasta-id ID_DA_PASTA --planilha "…xlsx" --videos pesquisas/[produto]/videos`. Se já existir na pasta uma pesquisa do mesmo produto e ângulo (`search_files` pelo nome), **atualize-a** com `--atualizar ID_DA_PLANILHA` — mesmo link, e a versão anterior fica no Histórico de versões do Sheets; antes, exporte-a e confira se há texto do Oséias nas colunas amarelas (se houver, avise e não sobrescreva sem ele aprovar). Sem pesquisa anterior, o script sobe a planilha **convertida em Planilha Google** (nome repetido ganha data e hora) e os vídeos na subpasta `Referências (vídeos)`. Depois exporte a planilha convertida e confira fórmulas, listas e IDs (testado 2026-11-25: conversão íntegra, 8 vídeos/46 MB em 32 s). Não use o `create_file` do Drive MCP para isso: ele exige o arquivo em base64 dentro da conversa. Atualize a coluna 'Vídeo no Drive' da aba Transcrições com os links devolvidos.
- Se for editar células direto no Google Sheets (pt-BR), fórmulas com `;` → `=DATE(2026;11;24)`, `=COUNTIF(R5:R1000;T46)` (referências absolutas em `references/planilha.md`), e `'` antes de ID e de texto que começa com `= + - @ '`.
- IDs da Meta sempre como texto (no JSON, string); categorias dos dropdowns = as da amostra.

## Passo 7 — Verificar (obrigatório) e entregar
Releia a planilha e confira:
- [ ] as 10 abas com os nomes e a ordem de `references/planilha.md`; cabeçalho na linha 4 com os nomes literais
- [ ] ≥10 referências na aba A, cada uma com link (`?id=`), `Tempo rodando` e `Dias ativos` por fórmula (data da consulta em N2, fixa, menos `DATE(...)` — ver `references/planilha.md`)
- [ ] colunas amarelas (A: I · Transcrições: S · Amostra: K, L e S · B-E: E · F: E) pintadas e, salvo Transcrições S, vazias
- [ ] dropdowns preenchidos só com valores da lista; os blocos de contadores (A: T:V · Amostra: U:W, por marca, formato, ângulo, mecanismo e prova) somam o total de linhas
- [ ] aba *Amostra concorrentes* (não mais *Amostra 3 marcas*) com o quadro *Concorrentes diretos* (U4) preenchido: até 5 marcas, cada uma com produto, preço visto (ou `n/v`), mecanismo, **por que é concorrente direto**, link `view_all_page_id` e contagem de anúncios ativos > 0; nomes do quadro iguais aos da coluna Marca
- [ ] nenhuma fórmula com erro (#ERROR!, #NAME?, #VALUE!) e IDs sem notação científica (nada de `2,54937E+15`)
- [ ] toda frase de cliente tem link e marcação `Marca [marca]`/`Genérico`
- [ ] nenhuma palavra proibida (ver regras)
- [ ] claims do produto só da página oficial (aba Produto, com fonte)
- [ ] bloqueios registrados em *IA e o que travou*; fontes com URL em *Fontes*

Entrega no chat (até 10 linhas): 3–5 achados acionáveis, principais limitações, link/arquivo da planilha. Ofereça a etapa 2: o brief, **no modelo de `references/brief.md`** (perguntas Psychology → Production → CTA, um brief por hipótese de teste).

## Se o Oséias tiver swipe
Referências que ele aprovar entram no swipe dele (aba *Índice*) no formato que já existe lá — só com aprovação.
