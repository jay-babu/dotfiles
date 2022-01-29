#!/usr/bin/env zsh

/home/linuxbrew/.linuxbrew/bin/brew tap ethereum/ethereum
/home/linuxbrew/.linuxbrew/bin/brew install zsh gcc node@16 exa gh openjdk@11 neovim fzf bat protobuf go gitui cheat solidity tmux fish fisher
bash /home/linuxbrew/.linuxbrew/bin/brew/opt/fzf/install

go install github.com/google/wire/cmd/wire@latest
go install google.golang.org/grpc/cmd/protoc-gen-go-grpc@latest
go install google.golang.org/protobuf/cmd/protoc-gen-go@latest

mkdir -p ~/.zsh

ln -sf "$(pwd)"/.zshrc ~/.zshrc
ln -sf "$(pwd)"/.tmux.conf ~/.tmux.conf
ln -sf "$(pwd)"/.p10k.zsh ~/.p10k.zsh
ln -sf "$(pwd)"/submodules ~/.zsh

(npm install -g npm@latest && npm install -g neovim)&

mkdir -p ~/.config/gitui
ln -sf "$(pwd)"/key_bindings.ron ~/.config/gitui

git config --global user.email "36803168+jayp0521@users.noreply.github.com"
git config --global user.name "Jay Patel"

git submodule add -f https://github.com/zsh-users/zsh-syntax-highlighting.git submodules/zsh-syntax-highlighting

git submodule add -f https://github.com/zsh-users/zsh-autosuggestions submodules/zsh-autosuggestions

git submodule add -f https://github.com/zsh-users/zsh-completions.git submodules/zsh-completions

git submodule add -f https://github.com/romkatv/powerlevel10k.git submodules/powerlevel10k

git submodule update --recursive --remote
