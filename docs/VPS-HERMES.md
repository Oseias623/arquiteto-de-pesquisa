# Rodar no Hermes Agent numa VPS

O [Hermes Agent](https://hermes-agent.nousresearch.com/docs) usa o mesmo formato de skill que o Claude Code: uma pasta com `SKILL.md`, `references/` e `scripts/`. Por isso a skill entra no Hermes sem conversão; basta criar um link em `~/.hermes/skills/`.

## 1. Preparar a VPS
- **Sistema:** Ubuntu 22.04 ou 24.04.
- **Máquina:** 2 vCPU e 4 GB de RAM no mínimo. O whisper `small` usa cerca de 1 GB.
- **Disco:** 10 GB livres. Os vídeos de cada pesquisa ocupam cerca de 100 MB.
- **Segurança, antes de tudo:**
  - Crie um usuário comum e entre por chave SSH, com o login por senha desligado.
  - Ative o firewall liberando só o SSH: `sudo ufw allow OpenSSH && sudo ufw enable`.
  - **Nunca** abra para a internet a porta do navegador, de VNC ou de depuração (9222). Para acessar, use um túnel SSH (passo 3).

## 2. Instalar
```sh
git clone https://github.com/Oseias623/arquiteto-de-pesquisa.git && cd arquiteto-de-pesquisa
sh scripts/instalar_vps.sh        # apt, yt-dlp+curl-cffi, whisper.cpp, Chromium, link da skill no Hermes
sh scripts/verificar_ambiente.sh
```
Para clonar um repositório privado, entre antes com `gh auth login` ou use uma *deploy key* só de leitura. Não cole token na URL do git.

Depois, inicie o Hermes **na pasta do repositório**, para os scripts acharem os caminhos relativos e o `AGENTS.md`. Rode `hermes` e peça a pesquisa normalmente.

## 3. Fazer os logins na VPS
**Google Drive (gcloud).** Funciona sem tela:
```sh
gcloud auth login --enable-gdrive-access --no-launch-browser
```
Abra o link no seu computador, entre com a conta editora da pasta e cole o código **como texto** no terminal da VPS.

**Navegador (Facebook, Reddit e TikTok).** **No modo híbrido, pule esta parte:** a VPS não navega. Só faça isto se quiser a VPS coletando sozinha. A VPS não tem tela. O login é feito uma vez, pelo seu Chrome, através de um túnel SSH:
1. Na VPS, abra o Chromium sem tela, com perfil fixo e porta de depuração **só em localhost**:
   ```sh
   CHROME=$(ls -d ~/.cache/ms-playwright/chromium-*/chrome-linux*/chrome | head -1)
   "$CHROME" --headless=new --remote-debugging-address=127.0.0.1 --remote-debugging-port=9222 \
     --user-data-dir="$HOME/.playwright-pesquisa" https://www.facebook.com
   ```
2. No seu computador, abra o túnel: `ssh -N -L 9222:localhost:9222 usuario@vps`.
3. No seu Chrome:
   - abra `chrome://inspect` › *Configure…* e adicione `localhost:9222`;
   - clique em *inspect* na aba que aparecer, o que mostra a tela da VPS e permite clicar e digitar;
   - faça login no Facebook, no Reddit e no TikTok, abrindo cada site pela barra de endereço da própria tela.
4. Feche o Chromium na VPS (Ctrl+C). A sessão fica salva no perfil.
5. Aponte o navegador do Hermes para esse perfil: Playwright MCP com `--user-data-dir ~/.playwright-pesquisa` e `--headless`.

Esse perfil vale como senha: deixe a pasta com `chmod 700` e nunca a copie para o repositório.

## Modo híbrido (o modo escolhido)
A divisão é por quem acessa a internet:

| Mac (Overclock, IP de casa) | VPS (Hermes, sem navegador) |
|---|---|
| produto, palavras-chave, Biblioteca da Meta, concorrentes | transcrição dos vídeos (whisper) |
| Reddit, TikTok, comentários do YouTube e do TikTok | síntese: padrões, lacunas, big idea |
| classificação e **download** dos 10–12 vídeos | planilha, upload no Drive e conferência |

Os dados vão do Mac para a VPS por **SSH** (`scripts/sincronizar.sh`) e não passam pelo GitHub. O código vai pelo Git, com `git pull` nas duas máquinas.

### Ligar uma vez (no Mac)
1. Crie uma chave só para isso e instale na VPS:
   ```sh
   ssh-keygen -t ed25519 -f ~/.ssh/pesquisa_vps -C pesquisa-vps
   ssh-copy-id -i ~/.ssh/pesquisa_vps.pub usuario@IP_DA_VPS
   ```
2. Em `~/.ssh/config`, coloque:
   ```
   Host pesquisa-vps
     HostName IP_DA_VPS
     User usuario
     IdentityFile ~/.ssh/pesquisa_vps
   ```
3. No `.env` do repositório no Mac (fora do Git), coloque `PESQUISA_VPS=pesquisa-vps:arquiteto-de-pesquisa`.
4. Rode `sh scripts/sincronizar.sh testar`. A resposta esperada é `ok: VPS e repositório encontrados`.

Na VPS, o único login necessário é o do `gcloud` (passo 3), para subir no Drive. A VPS não precisa de Facebook, Reddit nem TikTok.

### Usar
1. **No Mac (Overclock):** peça a pesquisa no modo híbrido, por exemplo: "pesquisa o produto X, modo híbrido". O orquestrador coleta tudo, baixa os vídeos e roda `sincronizar.sh enviar <produto>`.
2. **Na VPS (Hermes, por SSH ou pelo canal que você ligou ao Hermes):** peça "processa a pesquisa <produto>". O Hermes transcreve, sintetiza, monta a planilha e atualiza o Drive.
3. **Opcional:** para trazer de volta ao Mac, rode `sh scripts/sincronizar.sh receber <produto>`.

## 4. Por que híbrido: IP de datacenter
A Meta, o Reddit, o TikTok e o YouTube bloqueiam muito mais os IPs de servidor do que o IP de casa. Na prática:

| Etapa | Na VPS |
|---|---|
| Montar a planilha, subir no Drive, transcrever com whisper | funciona |
| Comentários do YouTube (yt-dlp) | costuma pedir "confirme que não é um robô" |
| Comentários do TikTok (curl_cffi) | pode ser bloqueado |
| Biblioteca da Meta, Reddit e TikTok pelo navegador | alta chance de bloqueio ou de a conta pedir verificação |

Há três saídas, da mais simples para a mais robusta:
1. **Híbrido (recomendado):** as etapas de navegador rodam no seu Mac (Overclock), e a VPS fica com scripts, transcrição, síntese e Drive. O Git sincroniza o código, e os JSON da pesquisa passam pelo Drive ou por `rsync`.
2. **Proxy residencial:** exporte `HTTPS_PROXY` / `HTTP_PROXY` no ambiente do Hermes. O yt-dlp e os scripts em Python respeitam essas variáveis. A credencial do proxy vai só no `.env`, com `chmod 600`.
3. **Navegador na nuvem (Browserbase):** o Hermes tem plugin para isso. A sessão logada fica no serviço, com IP e impressão digital de navegador real.

## 5. Regras de segurança na VPS
- `.env` com `chmod 600`, perfil do navegador com `chmod 700`, e as duas coisas fora do Git. O `.gitignore` e o hook já barram isso.
- Para rodar com agenda (cron do Hermes), use as mesmas regras: navegador só lê, no máximo 2 navegadores, a Meta em série e o Drive só manda para a lixeira.
- Se a VPS for comprometida, revogue os acessos:
  - Google: `gcloud auth revoke` e myaccount.google.com › Segurança.
  - Redes sociais: encerre as sessões no Facebook, no Reddit e no TikTok.
