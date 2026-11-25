# Instalar o agente: Claude Code ou Codex

Este projeto roda num **agente que funciona no seu computador**. Escolha o que combina com a assinatura que você já tem:

| Você assina | Instale | Seção |
|---|---|---|
| **Claude** (Pro ou Max) | Claude Code | [A](#a-claude-code) |
| **ChatGPT** (Plus, Pro, Business…) | Codex | [B](#b-codex) |
| Os dois | Qualquer um; os dois rodam a skill | — |

O chat comum (claude.ai ou chatgpt.com no navegador) **não** roda a pesquisa: ele não abre o terminal, não baixa vídeos e não acessa o navegador logado. Depois de pronta a planilha, ele serve para escrever briefs e advertoriais.

> Os comandos abaixo eram os oficiais em novembro de 2026. Se algum não funcionar, confira na página oficial que está no link de cada seção.

---

## 0. Antes: abrir o terminal

- **Mac:** aperte `Cmd + Espaço`, digite **Terminal** e dê Enter.
- **Windows:** o projeto usa scripts de Linux, então use o **WSL** (um Ubuntu dentro do Windows):
  1. Abra o **PowerShell como administrador**: clique com o botão direito no menu Iniciar e escolha *Terminal (Admin)*.
  2. Rode `wsl --install` e reinicie o computador.
  3. Abra o app **Ubuntu** no menu Iniciar e crie um usuário e uma senha.

  Todos os comandos deste guia são digitados **dentro do Ubuntu**.

Instale também o Node.js, que os dois agentes e o navegador automático usam:
- **Mac:** primeiro o Homebrew, se ainda não tiver:
  ```sh
  /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
  ```
  Depois:
  ```sh
  brew install node git
  ```
- **Windows (Ubuntu/WSL):**
  ```sh
  sudo apt update && sudo apt install -y nodejs npm git
  ```

---

## A. Claude Code

Página oficial: https://docs.claude.com/en/docs/claude-code

1. **Instalar.** Use o mesmo comando no Mac e no Ubuntu/WSL:
   ```sh
   curl -fsSL https://claude.ai/install.sh | bash
   ```
   Se der erro, use a alternativa: `npm install -g @anthropic-ai/claude-code`.
2. **Entrar.** Rode `claude`. Na primeira vez, ele abre o navegador: entre com a **mesma conta do claude.ai** (Pro ou Max).
3. **Testar.** Digite `oi` e veja se ele responde. Para sair, use `/exit`.

**Sem terminal:** o app **Claude para desktop** (https://claude.ai/download) também traz o Claude Code. Abra o app, vá à aba **Code** e escolha a pasta do projeto.

**Navegador para a pesquisa (uma vez):**
```sh
claude mcp add playwright -- npx @playwright/mcp@latest --user-data-dir ~/.playwright-pesquisa
```
Outra opção é a extensão **Claude in Chrome**, com o Chrome logado no Facebook, no Reddit e no TikTok.

---

## B. Codex

Página oficial: https://developers.openai.com/codex

1. **Instalar:**
   - Mac: `brew install --cask codex`, ou `npm install -g @openai/codex`
   - Ubuntu/WSL: `npm install -g @openai/codex` (se pedir permissão, use `sudo npm install -g @openai/codex`)
2. **Entrar.** Rode `codex` e escolha **Sign in with ChatGPT**. Entre com a **mesma conta do ChatGPT**. Não precisa de chave de API.
3. **Testar.** Digite `oi` e veja se ele responde. Para sair, aperte `Ctrl + C`.

**Navegador para a pesquisa (uma vez):** abra o arquivo de configuração:
```sh
mkdir -p ~/.codex && nano ~/.codex/config.toml
```
Cole isto no arquivo:
```toml
[mcp_servers.playwright]
command = "npx"
args = ["@playwright/mcp@latest", "--user-data-dir", "~/.playwright-pesquisa"]
```
Salve com `Ctrl + O`, Enter, e saia com `Ctrl + X`.

---

## C. Depois do agente: o projeto

1. **Baixar o projeto:**
   ```sh
   cd ~ && git clone https://github.com/Oseias623/arquiteto-de-pesquisa.git
   cd arquiteto-de-pesquisa
   ```
2. **Instalar as ferramentas da pesquisa:**
   - **Mac:**
     ```sh
     brew install python ffmpeg uv && python3 -m pip install --user openpyxl && uv tool install "yt-dlp[default,curl-cffi]"
     ```
   - **Ubuntu/WSL:** `sh scripts/instalar_vps.sh` instala tudo, inclusive a transcrição.
3. **Conferir.** Rode `sh scripts/verificar_ambiente.sh` e resolva o que aparecer como `[falta]`. Se quiser, peça ao agente: *"roda o verificar_ambiente e me ajuda a instalar o que falta"*.
4. **Logins**, feitos uma vez:
   - Na primeira pesquisa, a janela do navegador abre: entre no Facebook, no Reddit e no TikTok.
   - Para subir no **seu** Google Drive, siga o passo **Google Drive** do [README](../README.md#3-fazer-os-logins).
5. **Usar.** Dentro da pasta `arquiteto-de-pesquisa`, rode `claude` ou `codex` e peça:
   > Pesquisa o produto *[nome]* ([link oficial]), país [EUA], idioma [inglês], ângulo [dor], venda por [afiliado], destino: minha pasta do Drive [link].

## Problemas comuns
| Sintoma | O que fazer |
|---|---|
| `command not found: claude` ou `codex` | Feche e abra o terminal de novo. Se continuar, use o comando `npm install -g …` da seção do agente. |
| `npm: permission denied` (Ubuntu) | Repita com `sudo` na frente. |
| O login não abre o navegador | Copie o link que aparece no terminal e abra à mão. |
| O agente pede permissão para rodar comandos | É normal. Leia e aprove: ele só lê sites, não posta nada. |
