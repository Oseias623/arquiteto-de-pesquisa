# Arquiteto de pesquisa

Este projeto faz pesquisa automática de anúncios por produto. Você informa o produto, o país e a dor. O agente então:
- varre a Biblioteca de Anúncios da Meta;
- levanta até 5 concorrentes diretos;
- coleta a voz do cliente no YouTube, no TikTok e no Reddit;
- baixa e transcreve 10–12 anúncios de referência.

O resultado é uma planilha de 10 abas com referências, transcrições, padrões, lacunas e big idea, que pode subir direto para o Google Drive. A planilha é a base para escrever anúncios novos a partir do que já funciona.

Funciona no **Claude Code**, no **Overclock**, no **Codex**, no **Gemini CLI** e no **Hermes Agent** (inclusive numa VPS).

---

## Passo a passo para quem vai usar

### 1. Clonar
```sh
git clone https://github.com/Oseias623/arquiteto-de-pesquisa.git
cd arquiteto-de-pesquisa
git config core.hooksPath .githooks   # ativa a trava que impede commit de senha/token/dados
```

### 2. Instalar as ferramentas (uma vez)
| Ferramenta | Para quê | Como instalar (macOS) |
|---|---|---|
| Python 3.9+ e `openpyxl` | scripts e planilha | `python3 -m pip install --user openpyxl` |
| `yt-dlp` com `curl-cffi` | comentários do YouTube e do TikTok, vídeos da Meta | `uv tool install "yt-dlp[default,curl-cffi]"` (ou `pipx install …`) |
| `ffmpeg` | áudio e frames dos vídeos | `brew install ffmpeg` |
| `whisper.cpp` (opcional) | transcrição da fala | ver [Transcrição](#transcrição) |
| `gcloud` (opcional) | subir planilha e vídeos no Drive | `brew install --cask google-cloud-sdk` |

Depois confira o que ficou faltando:
```sh
sh scripts/verificar_ambiente.sh
```

### 3. Fazer os logins
Nenhum login fica salvo no repositório. Cada um fica no navegador ou na ferramenta.

1. **Navegador (Facebook, Reddit, TikTok).** A Biblioteca da Meta, a busca de comentários no Reddit e a busca de vídeos no TikTok passam por um navegador logado com a sua conta.
   - **Overclock:** abra o navegador do Overclock e entre nos três sites uma vez. A sessão fica guardada no app.
   - **Claude Code:** use a extensão Claude in Chrome com o Chrome logado, ou o Playwright MCP com perfil persistente (veja o passo 4).
   - **Codex / Gemini:** use o Playwright MCP com perfil persistente e faça login nos três sites na primeira vez que a janela abrir.

   O agente só **lê**: ele não curte, não segue, não comenta e não clica em botões do TikTok.

2. **Google Drive (opcional, para subir direto).** A conta que você usar precisa ser **Editora** da pasta de destino no Drive. Se a pasta for de outra conta, peça ao dono para compartilhá-la com você como Editor.
   ```sh
   gcloud auth login --enable-gdrive-access --no-launch-browser
   ```
   - Abra o link que aparecer e entre com a conta editora.
   - **Copie o código como texto** e cole no terminal. Não use print: a leitura da imagem pode trocar caracteres.
   - Cada código só vale para o link que o gerou. Se rodar o comando de novo, use o código novo.
   - **Nunca** cole esse código em chat, issue ou arquivo.

   Sem o gcloud, a planilha sai como `.xlsx` em `pesquisas/<produto>/` e você sobe à mão.

3. **Reddit por API (opcional).** Se tiver um app do Reddit, copie `.env.example` para `.env` e preencha. O `.env` nunca vai para o Git. Sem ele, o Reddit é lido pelo navegador logado.

### 4. Ligar no seu agente
- **Claude Code:** já funciona. A skill fica em `.claude/skills/pesquisa-produto-automatica/` e os subagentes em `.claude/agents/`. Para o navegador:
  - Claude in Chrome, ou
  - `claude mcp add playwright -- npx @playwright/mcp@latest --user-data-dir ~/.playwright-pesquisa`
- **Overclock:** já funciona. O orquestrador abre um pane por trabalhador e usa o navegador interno.
- **Codex:** lê o `AGENTS.md` e encontra a skill em `.agents/skills/`. Para o navegador, coloque isto em `~/.codex/config.toml`:
  ```toml
  [mcp_servers.playwright]
  command = "npx"
  args = ["@playwright/mcp@latest", "--user-data-dir", "~/.playwright-pesquisa"]
  ```
- **Gemini CLI:** lê o `GEMINI.md`, que importa o `AGENTS.md`. Para o navegador, coloque isto em `.gemini/settings.json`:
  ```json
  { "mcpServers": { "playwright": { "command": "npx", "args": ["@playwright/mcp@latest", "--user-data-dir", "~/.playwright-pesquisa"] } } }
  ```

- **Hermes Agent (VPS):** usa o mesmo formato de skill. `sh scripts/instalar_vps.sh` instala tudo e liga a skill em `~/.hermes/skills/`. Para usar no **modo híbrido** (o Mac coleta, a VPS processa), veja os passos em [docs/VPS-HERMES.md](docs/VPS-HERMES.md).

### 5. Rodar
Abra o agente na pasta do repositório e peça, por exemplo:

> Pesquisa o produto *Dr. C. Tuna Lumi Radiance Brightening Serum* (link oficial …), ângulo dark spots, EUA, inglês, venda por afiliado, destino: pasta do Drive <link>.

O agente pergunta só o que faltar. O resultado sai em `pesquisas/<produto>/` e, com o gcloud logado, também no Drive.

---

## Transcrição
O whisper.cpp é compilado a partir do código-fonte, sem precisar de sudo:
```sh
git clone https://github.com/ggml-org/whisper.cpp ~/.local/src/whisper.cpp
cd ~/.local/src/whisper.cpp && cmake -B build && cmake --build build -j --config Release
mkdir -p ~/.local/bin ~/.cache/whisper-cpp && ln -sf "$PWD/build/bin/whisper-cli" ~/.local/bin/whisper-cli
sh ./models/download-ggml-model.sh small && mv models/ggml-small.bin ~/.cache/whisper-cpp/
```
Sem o whisper, a transcrição sai pelas legendas queimadas no vídeo, e a planilha registra isso na aba *Cobertura*.

## O que vai e o que não vai para o Git
| Vai | Não vai (`.gitignore` + trava no pre-commit) |
|---|---|
| skill, subagentes, scripts, referências, README | `.env`, tokens, chaves, credenciais |
| `.env.example` (só com nomes, sem valores) | `pesquisas/` (dados coletados, vídeos, planilhas) |
| | `gabarito/` (pesquisas antigas), `*.zip`, `*.mp4`, `*.xlsx` |

Se o hook barrar um commit, ele mostra o arquivo ou o trecho suspeito. Tire do commit com `git restore --staged <arquivo>` e tente de novo.

## Estrutura
```
AGENTS.md / CLAUDE.md / GEMINI.md     instruções de entrada para cada CLI
.claude/skills/pesquisa-produto-automatica/
  SKILL.md                            roteiro do orquestrador
  references/regras.md · planilha.md  regras de conteúdo e esquema das 10 abas
  scripts/                            voz_cliente/, transcrever.py, montar_planilha.py, subir_drive.py, adicionar_ao_swipe.py
.claude/agents/                       papéis: varredor-meta, pesquisador-produto, coletor-voz-cliente,
                                      classificador-referencias, transcritor, sintetizador
.agents/skills/                       atalho (link) para a mesma skill, para o Codex
scripts/verificar_ambiente.sh         confere ferramentas e logins
scripts/instalar_vps.sh               instala tudo numa VPS Ubuntu e liga a skill no Hermes
scripts/sincronizar.sh                modo híbrido: envia/recebe a pasta da pesquisa Mac ⇄ VPS por SSH
```

## Atualizações
Toda melhoria na skill vira um commit neste repositório. Para trazer as mudanças em outra máquina, rode `git pull`.
