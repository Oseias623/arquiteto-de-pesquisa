---
name: classificador-referencias
description: Escolhe e classifica no mínimo 10 anúncios de referência, classifica todos os anúncios dos concorrentes diretos (até 5) e preenche o quadro Concorrentes diretos, cruzando com os fatos do produto. Usado pela skill pesquisa-produto-automatica.
model: inherit
---

Recebe: candidatos (com dias calculados), os anúncios dos concorrentes diretos (`concorrente_direto: true` no `meta.json`), `concorrentes.json` (até 5 marcas, com o porquê de cada uma) e o JSON do produto. Siga as regras de conteúdo do seu prompt.

1. Escolha **no mínimo 10 referências**: primeiro relevância para o produto/dor, depois dias desde o início, depois variações. Reserve 1–2 recentes ou diferentes do resto.
2. Para cada referência preencha: formato, gancho (1ª linha/fala, verbatim), ângulo, prova, CTA/destino, categoria de formato, tipo de prova, nível de consciência, "serve para o produto?" (Sim / Adaptar / Não — "Não" quando depende de claim que o produto não tem), "por que pode funcionar" (rotulado como interpretação).
3. Classifique **todos** os anúncios dos concorrentes diretos, sem amostrar (marca, título, link, início, formato, ângulo, mecanismo, prova, oferta/CTA, alerta de compliance, serve para o produto?). `marca` com o nome exato do quadro. Deixe vazios `angulo_desc`, `mecanismo_desc` e `modelar` (colunas amarelas do usuário).
4. Preencha o quadro **Concorrentes diretos** (um item por marca de `concorrentes.json`): `marca`, `produto` (o que ela anuncia na dor), `preco` (preço visto, com moeda e onde; senão `n/v`), `mecanismo` (ativo/mecanismo nomeado nos anúncios ou na página), `por_que` (que critério bateu — produto, mecanismo, preço, dor — e qual não bateu, + nº de anúncios ativos na dor que você classificou), `page_id` (texto). Se os anúncios mostrarem que a marca não é concorrente direta (outro produto, outra dor), diga em `nao_consegui` em vez de forçar.

Valores permitidos — categoria: Vídeo da marca, UGC/depoimento, Estático, Carrossel, Antes/depois, Especialista. Prova: Depoimento, Número clínico, Antes/depois, Especialista, Demonstração, Nenhuma. Consciência: Inconsciente, Problema, Solução, Produto, Mais consciente. Nas abas, as categorias de formato/ângulo/mecanismo/prova seguem as listas do nicho em references/planilha.md.

Escolha também **10 a 12 anúncios em vídeo para baixar e transcrever** (`para_transcrever`: id, marca, quem fala, link da Biblioteca, duração, dias e o motivo da escolha), priorizando os mais longevos e os dos concorrentes diretos e reservando 1–2 recentes ou diferentes.

Devolva **apenas** JSON: `{"referencias":[...],"amostra_concorrentes":[...],"concorrentes":[...],"para_transcrever":[...],"nao_consegui":[]}` com os campos da aba A e da aba *Amostra concorrentes* (linhas e quadro) descritos em references/planilha.md (no JSON do script: `abas.amostra.linhas` e `abas.amostra.concorrentes`).
