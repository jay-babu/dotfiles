#!/usr/bin/env bash

apt install exa nodejs-lts gh neovim fzf bat protobuf golang solidity tmux fish ripgrep stylua luarocks git python

luarocks install luacheck

go install github.com/google/wire/cmd/wire@latest
go install google.golang.org/grpc/cmd/protoc-gen-go-grpc@latest
go install google.golang.org/protobuf/cmd/protoc-gen-go@latest
go install mvdan.cc/sh/v3/cmd/shfmt@latest

(npm install -g npm@latest && npm install -g neovim bash-language-server vscode-langservers-extracted graphql-language-service-cli solidity-language-server typescript-language-server solc)&
(python -m pip install --upgrade pip && pip3 install --upgrade pynvim pyright)&

git config --global user.email "36803168+jayp0521@users.noreply.github.com"
git config --global user.name "Jay Patel"

