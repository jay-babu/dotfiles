#!/usr/bin/env bash

/home/linuxbrew/.linuxbrew/bin/brew tap ethereum/ethereum
/home/linuxbrew/.linuxbrew/bin/brew install zsh gcc node@16 exa gh openjdk@11 neovim fzf bat protobuf go gitui cheat solidity tmux fish fisher ripgrep stylua luarocks shellcheck lua-language-server

luarocks install luacheck

go install github.com/google/wire/cmd/wire@latest
go install google.golang.org/grpc/cmd/protoc-gen-go-grpc@latest
go install google.golang.org/protobuf/cmd/protoc-gen-go@latest
go install mvdan.cc/sh/v3/cmd/shfmt@latest

(npm install -g npm@latest && npm install -g neovim bash-language-server vscode-langservers-extracted graphql-language-service-cli solidity-language-server typescript-language-server)&
(pip3 install --upgrade pynvim pyright)&

git config --global user.email "36803168+jayp0521@users.noreply.github.com"
git config --global user.name "Jay Patel"

fish_add_path /home/linuxbrew/.linuxbrew/bin 
fish_add_path /home/linuxbrew/.linuxbrew/opt/node@16/bin
fish_add_path /home/linuxbrew/.linuxbrew/opt/openjdk@11/bin
fish_add_path /home/linuxbrew/.linuxbrew/opt/nvim/bin
fish_add_path "$(go env GOPATH)"/bin

set -gx FZF_DEFAULT_OPTS='--hidden --preview "bat --style=numbers --color=always --line-range :500 {}"'

