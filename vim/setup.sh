#!/usr/bin/env zsh

brew install neovim universal-ctags virtualenv node@16 ripgrep fd

mkdir -p ~/.config/nvim

ln -sf "$(pwd)"/init.vim ~/.config/nvim

mkdir pack

mkdir -p ~/.local/share/nvim/site

ln -sf "$(pwd)"/pack ~/.local/share/nvim/site

git submodule add -f https://github.com/ryanoasis/vim-devicons.git pack/plugins/start/vim-devicons

git submodule add -f https://github.com/navarasu/onedark.nvim.git pack/plugins/start/onedark.nvim

git submodule add -f https://github.com/simeji/winresizer.git pack/plugins/start/winresizer

git submodule add -f https://github.com/blackCauldron7/surround.nvim.git pack/plugins/start/surround.nvim

git submodule add -f https://github.com/ms-jpq/chadtree.git pack/plugins/start/chadtree

git submodule add -f https://github.com/neovim/nvim-lspconfig.git pack/lsp/start/nvim-lspconfig

git submodule add -f https://github.com/ms-jpq/coq_nvim.git pack/lsp/start/coq_nvim

git submodule add -f https://github.com/ms-jpq/coq.artifacts.git pack/lsp/start/coq.artifacts

git submodule add -f https://github.com/ms-jpq/coq.thirdparty.git pack/lsp/start/coq.thirdparty

git submodule add -f https://github.com/ray-x/lsp_signature.nvim.git pack/lsp/start/lsp_signature.nvim

git submodule add -f https://github.com/rmagatti/goto-preview.git pack/lsp/start/goto-preview

git submodule add -f https://github.com/glepnir/dashboard-nvim.git pack/plugins/start/dashboard-nvim

git submodule add -f https://github.com/nvim-lua/plenary.nvim.git pack/plugins/start/plenary.nvim

git submodule add -f https://github.com/nvim-telescope/telescope.nvim.git pack/plugins/start/telescope.nvim

git submodule add -f https://github.com/nvim-treesitter/nvim-treesitter.git pack/plugins/start/nvim-treesitter

git submodule add -f https://gitlab.com/yorickpeterse/nvim-window.git pack/plugins/start/nvim-window

git submodule add -f https://github.com/p00f/nvim-ts-rainbow.git pack/plugins/start/nvim-ts-rainbow

git submodule add -f https://github.com/nvim-lualine/lualine.nvim.git pack/plugins/start/lualine.nvim

git submodule add -f https://github.com/kyazdani42/nvim-web-devicons.git pack/plugins/start/nvim-web-devicons

git submodule add -f https://github.com/windwp/nvim-ts-autotag.git pack/lsp/start/nvim-ts-autotag

git submodule add -f https://github.com/nvim-treesitter/nvim-treesitter-refactor.git pack/lsp/start/nvim-treesitter-refactor

git submodule add -f https://github.com/ruifm/gitlinker.nvim.git pack/plugins/start/gitlinker.nvim

git submodule add -f https://github.com/tanvirtin/vgit.nvim.git pack/plugins/start/vgit.nvim

git submodule add -f https://github.com/psliwka/vim-smoothie.git pack/plugins/start/vim-smoothie

git submodule add -f https://github.com/akinsho/bufferline.nvim.git pack/plugins/start/bufferline.nvim

git submodule add -f https://github.com/TovarishFin/vim-solidity.git pack/plugins/start/vim-solidity

git submodule update --recursive --remote

