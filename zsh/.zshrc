# Enable Powerlevel10k instant prompt. Should stay close to the top of ~/.zshrc.
# Initialization code that may require console input (password prompts, [y/n]
# confirmations, etc.) must go above this block; everything else may go below.
if [[ -r "${XDG_CACHE_HOME:-$HOME/.cache}/p10k-instant-prompt-${(%):-%n}.zsh" ]]; then
  source "${XDG_CACHE_HOME:-$HOME/.cache}/p10k-instant-prompt-${(%):-%n}.zsh"
fi


ZSH_PREFIX="~/.zsh"

export ZSH="/home/jay/.oh-my-zsh"
export DONT_PROMPT_WSL_INSTALL=true

eval "$(/home/linuxbrew/.linuxbrew/bin/brew shellenv)"
export PATH="/home/linuxbrew/.linuxbrew/opt/node@16/bin:$PATH"
export PATH="/home/linuxbrew/.linuxbrew/opt/openjdk@11/bin:$PATH"
export PATH="/home/linuxbrew/.linuxbrew/opt/nvim/bin:$PATH"
export PATH="/home/linuxbrew/.linuxbrew/bin:$PATH"
export PATH="$PATH:$(go env GOPATH)/bin"
export FZF_DEFAULT_OPTS='--hidden --preview "bat --style=numbers --color=always --line-range :500 {}"'

[ -z "$PS1" ] && return

function cd {
    builtin cd "$@" && exa
}

function vim {
    nvim "$@"
}

# ZSH_THEME="robbyrussell"

zstyle ':omz:update' mode auto      # update automatically without asking
[ -f ~/.fzf.zsh ] && source ~/.fzf.zsh

plugins=(
    git
    wd
    sudo
    web-search
    copybuffer
    dirhistory
    jsontools
    safe-paste
    vi-mode
)

source $ZSH/oh-my-zsh.sh

source ~/.zsh/submodules/zsh-syntax-highlighting/zsh-syntax-highlighting.zsh
source ~/.zsh/submodules/zsh-autosuggestions/zsh-autosuggestions.zsh
source ~/.zsh/submodules/powerlevel10k/powerlevel10k.zsh-theme

fpath=("${ZSH_PREFIX}"/submodules/zsh-completions/src $fpath)

export EDITOR=/home/linuxbrew/.linuxbrew/bin/nvim

# To customize prompt, run `p10k configure` or edit ~/.p10k.zsh.
[[ ! -f ~/.p10k.zsh ]] || source ~/.p10k.zsh

