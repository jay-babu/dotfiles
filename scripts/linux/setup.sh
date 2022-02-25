#!/usr/bin/env fish

brew tap ethereum/ethereum
brew install zsh gcc node@16 exa gh openjdk@11 neovim fzf bat protobuf go gitui cheat solidity tmux fish fisher ripgrep stylua luarocks shellcheck lua-language-server

luarocks install luacheck

go install github.com/google/wire/cmd/wire@latest
go install google.golang.org/grpc/cmd/protoc-gen-go-grpc@latest
go install google.golang.org/protobuf/cmd/protoc-gen-go@latest
go install mvdan.cc/sh/v3/cmd/shfmt@latest

chmod u+x ./tools.sh
./tools.sh &

git config --global user.email "36803168+jayp0521@users.noreply.github.com"
git config --global user.name "Jay Patel"
