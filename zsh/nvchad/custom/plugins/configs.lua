local M = {}

M.treesitter = {
   ensure_installed = {
      "c",
      "css",
      "dockerfile",
      "go",
      "graphql",
      "html",
      "javascript",
      "json",
      "lua",
      "python",
      "toml",
      "vim",
   },
}

M.nvimtree = {
   git = {
      enable = true,
   },
}

M.bufferline = {
  options = {
    diagnostics = "nvim_lsp",
  },
}

return M

