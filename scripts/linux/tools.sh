#!/usr/bin/env bash

if ! command -v brew &>/dev/null; then
	/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
fi

(npm install -g npm@latest && npm install -g neovim bash-language-server vscode-langservers-extracted graphql-language-service-cli solidity-language-server typescript-language-server) &
(pip3 install --upgrade pynvim pyright) &
