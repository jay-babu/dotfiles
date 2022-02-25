#!/usr/bin/env bash

(npm install -g npm@latest && npm install -g neovim bash-language-server vscode-langservers-extracted graphql-language-service-cli solidity-language-server typescript-language-server) &
(pip3 install --upgrade pynvim pyright) &
