# Brief (etapa 2) — modelo do Oséias

Faça o brief **só quando o Oséias pedir**, e um brief por anúncio, ou seja, por hipótese de teste. A fonte é a planilha da pesquisa. Não use nada que não esteja nela ou na página oficial.

## Modelo (perguntas literais, nesta ordem)

```
Psychology →
Who is this ad speaking to?
What level of awareness is this audience at?
What is the central idea of this ad?
What evidence led me to this idea? Why is this hypothesis worth testing, and why might it work?
What objection or belief must this ad address?
Which product claims can we support, and what evidence supports them?

Production →
What avatar will I use in this ad? Why?
What format will I use in this ad? Why?
Which visual reference will I use, and what evidence supports it?
  (até 4 referências, uma por linha)
New test (describe it here)
What exactly are we testing, against what comparison, and which metric will guide the next decision?

CTA →
Which advertorial or landing page should this ad lead to?
```

Uma pergunta sem resposta sustentada pela pesquisa fica como `To be defined`, com uma linha dizendo o que falta. Não invente.

## Como responder cada pergunta
| Pergunta | De onde sai na planilha | Regra |
|---|---|---|
| Who is this ad speaking to? | voz do cliente, padrões B, lacunas | público + situação + dor, nas palavras do público |
| Level of awareness | voz do cliente (o que já tentaram), padrões | Schwartz: inconsciente · consciente do problema · da solução · do produto · totalmente consciente, com o porquê |
| Central idea | F › Big idea (pista) ou uma lacuna | uma frase-direção, não a copy pronta |
| Evidence / why test | F › lacuna escolhida, aba A, Amostra, voz | separe **FATO** (com ID ou link) × **INTERPRETAÇÃO** × **HIPÓTESE** |
| Objection or belief | voz do cliente (objeções, marca) | 1–2 objeções, com frase verbatim e link |
| Product claims + evidence | aba Produto | só claim oficial, citado como a marca escreve (com asterisco), e a fonte; liste também o que **não** pode dizer |
| Avatar | Transcrições (quem fala), Amostra | quem aparece no vídeo e por que esse perfil serve ao público |
| Format | Transcrições (formato, estrutura), padrões C | formato + duração + estrutura, com a referência que o sustenta |
| Visual reference | aba A / Transcrições | até 4 referências: link `?id=`, marca, dias rodando e o que copiar (gancho visual, texto na tela, ritmo) |
| New test | F › hipótese de teste | variável única × controle, métrica principal e a regra de decisão (o que fazer se ganhar, perder ou empatar) |
| Landing page | aba Produto (loja de afiliado), padrões de CTA | URL do destino; se não houver advertorial, diga isso e use a página do produto na loja |

Antes de fechar o brief, confira se tudo o que ele recomenda (outro produto da linha, proteção, kit) está à venda no país e é declarado no rótulo. Não chame um teste de "mecanismo" (ver `advertorial.md`, lições 3, 4 e 9).

Valem as regras de `regras.md`: nada de palavras proibidas, frases de cliente sem autor e claims só da página oficial. Para afiliado, anote a divulgação obrigatória (FTC nos EUA).

## Idioma
**Tudo em inglês**, perguntas e respostas, para passar direto a criador ou editor americano. Frases de cliente e claims ficam verbatim. Os rótulos FATO, INTERPRETAÇÃO e HIPÓTESE viram FACT, INTERPRETATION e HYPOTHESIS. Use outro idioma só se o Oséias pedir.

## Entrega
1. Escreva `pesquisas/[produto]/Brief [n] - [short idea].md` em Markdown: `##` para Psychology, Production e CTA, pergunta em **negrito**, listas com `-`, e o asterisco de nota escapado como `\*`.
2. Suba como **Google Doc na pasta do produto** no Drive, ao lado da planilha. Use um upload multipart com a origem `text/markdown` e o destino `application/vnd.google-apps.document`, e o mesmo token do `gcloud` do `subir_drive.py`. O Drive converte títulos, negrito e listas.
3. Confira exportando como `text/plain`: não pode sobrar `**` nem `#`, e o `26%*` precisa aparecer com o asterisco.
