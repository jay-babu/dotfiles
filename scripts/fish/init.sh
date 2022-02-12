#!/usr/bin/env bash

curl -sL https://git.io/fisher | source && fisher install jorgebucaran/fisher

/home/linuxbrew/.linuxbrew/bin/brew install fish
echo "/home/linuxbrew/.linuxbrew/bin/fish" | sudo tee -a /etc/shells

