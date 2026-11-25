#!/bin/sh
# Modo híbrido: leva a pasta de uma pesquisa entre o Mac (coleta) e a VPS (processamento) por SSH.
# Os dados da pesquisa NUNCA passam pelo Git. Eles vão direto de máquina para máquina, criptografados pelo SSH.
#
# Uso (sempre no Mac, na raiz do repositório):
#   sh scripts/sincronizar.sh enviar  <produto>   # Mac → VPS (depois da coleta)
#   sh scripts/sincronizar.sh receber <produto>   # VPS → Mac (planilha, transcrições, síntese)
#   sh scripts/sincronizar.sh testar               # só confere a conexão
#
# Configuração: no .env (fora do Git), PESQUISA_VPS=usuario@host:caminho/do/repositorio
#   ex.: PESQUISA_VPS=oseias@203.0.113.10:arquiteto-de-pesquisa
# Login por chave SSH (ssh-copy-id usuario@host); nunca por senha em arquivo.
set -e
cd "$(dirname "$0")/.."
[ -f .env ] && PESQUISA_VPS=${PESQUISA_VPS:-$(sed -n 's/^PESQUISA_VPS=//p' .env | tail -1)}
[ -n "$PESQUISA_VPS" ] || { echo "Defina PESQUISA_VPS=usuario@host:caminho no .env"; exit 1; }
host=${PESQUISA_VPS%%:*}; rdir=${PESQUISA_VPS#*:}
[ "$host" != "$PESQUISA_VPS" ] || { echo "PESQUISA_VPS deve ter o formato usuario@host:caminho"; exit 1; }

acao=$1; prod=$2
SSH="ssh -o BatchMode=yes -o ConnectTimeout=10"
# Chave dedicada (criada no Mac em ~/.ssh/pesquisa_vps), se existir
[ -f "$HOME/.ssh/pesquisa_vps" ] && SSH="$SSH -i $HOME/.ssh/pesquisa_vps -o IdentitiesOnly=yes"
case "$acao" in
  testar)
    $SSH "$host" "test -d '$rdir/.claude/skills/pesquisa-produto-automatica' && echo 'ok: VPS e repositório encontrados'" \
      || { echo "falhou: confira a chave SSH (ssh-copy-id $host) e o caminho '$rdir'"; exit 1; } ;;
  enviar|receber)
    [ -n "$prod" ] || { echo "Informe o produto: sh scripts/sincronizar.sh $acao <produto>"; exit 1; }
    case "$prod" in */*|*..*|*" "*) echo "Nome de produto inválido (use o nome da pasta em pesquisas/)"; exit 1;; esac
    if [ "$acao" = enviar ]; then
      [ -d "pesquisas/$prod" ] || { echo "Não existe pesquisas/$prod"; exit 1; }
      $SSH "$host" "mkdir -p '$rdir/pesquisas/$prod' && chmod 700 '$rdir/pesquisas'"
      rsync -az --partial -e "$SSH" "pesquisas/$prod/" "$host:$rdir/pesquisas/$prod/"
    else
      mkdir -p "pesquisas/$prod"
      rsync -az --partial -e "$SSH" "$host:$rdir/pesquisas/$prod/" "pesquisas/$prod/"
    fi
    echo "ok: $acao pesquisas/$prod" ;;
  *) sed -n '5,8p' "$0"; exit 1 ;;
esac
