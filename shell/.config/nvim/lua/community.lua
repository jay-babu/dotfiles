-- AstroCommunity: import any community modules here
-- We import this file in `lazy_setup.lua` before the `plugins/` folder.
-- This guarantees that the specs are processed before any user plugins.

---@type LazySpec
return {
  { "AstroNvim/astrocommunity", version = "^13" },
  { import = "astrocommunity.recipes.telescope-nvchad-theme" },
  { import = "astrocommunity.pack.lua" },
  { import = "astrocommunity.quickfix.nvim-bqf" },
  { import = "astrocommunity.debugging.persistent-breakpoints-nvim" },
  { import = "astrocommunity.debugging.nvim-dap-repl-highlights" },
  { import = "astrocommunity.markdown-and-latex.render-markdown-nvim" },
  { import = "astrocommunity.completion.avante-nvim" },
  {
    "yetone/avante.nvim",
    optional = true,
    build = "make BUILD_FROM_SOURCE=true",
  },
  { import = "astrocommunity.diagnostics.trouble-nvim" },
  {
    import = "astrocommunity.editing-support.cutlass-nvim",
  },
  {
    "gbprod/cutlass.nvim",
    opts = function(_, opts)
      opts.exclude = vim.iter({ opts.exclude or {}, { "vx", "vX", "xx", "xX" } }):flatten():totable()
    end,
  },
  { import = "astrocommunity.editing-support.dial-nvim" },
  { import = "astrocommunity.editing-support.nvim-regexplainer" },
  {
    import = "astrocommunity.editing-support.treesj",
  },
  {
    "Wansmer/treesj",
    keys = { { "<leader>m", "<CMD>TSJToggle<CR>", desc = "Toggle Treesitter Join" } },
    opts = { max_join_length = 9999 },
  },
  { import = "astrocommunity.indent.indent-blankline-nvim" },
  { import = "astrocommunity.indent.mini-indentscope" },
  { import = "astrocommunity.motion.hop-nvim" },
  { import = "astrocommunity.motion.nvim-surround" },
  { import = "astrocommunity.motion.vim-matchup" },
  { import = "astrocommunity.scrolling.nvim-scrollbar" },
  { import = "astrocommunity.utility.noice-nvim" },
  { import = "astrocommunity.pack.docker" },
  { import = "astrocommunity.pack.go" },
  {
    "ray-x/go.nvim",
    event = function(_, _) return {} end,
  },
  { import = "astrocommunity.pack.json" },
  { import = "astrocommunity.pack.lua" },
  { import = "astrocommunity.pack.markdown" },
  { import = "astrocommunity.pack.python-ruff" },
  { import = "astrocommunity.pack.typescript" },
  { import = "astrocommunity.git.git-blame-nvim" },
  { import = "astrocommunity.pack.rust" },
  { import = "astrocommunity.pack.yaml" },
  { import = "astrocommunity.pack.bash" },
  { import = "astrocommunity.terminal-integration.vim-tmux-yank" },
  { import = "astrocommunity.syntax.vim-cool" },
  { import = "astrocommunity.lsp.lsp-inlayhints-nvim" },
  { import = "astrocommunity.editing-support.rainbow-delimiters-nvim" },
  { import = "astrocommunity.motion.nvim-spider" },
  { import = "astrocommunity.media.vim-wakatime" },
  { import = "astrocommunity.editing-support.nvim-regexplainer" },
  {
    "HiPhish/rainbow-delimiters.nvim",
    event = "VeryLazy",
    optional = true,
  },
  { import = "astrocommunity.editing-support.true-zen-nvim" },
  {
    "jay-babu/mason-null-ls.nvim",
    opts = {
      handlers = {
        clang_format = function() end,
      },
    },
  },
  -- { import = "astrocommunity.completion.copilot-lua-cmp" },
  { import = "astrocommunity.code-runner.overseer-nvim" },
  { import = "astrocommunity.recipes.telescope-nvchad-theme" },
  { import = "astrocommunity.recipes.vscode" },
  { import = "astrocommunity.git.gist-nvim" },
  { import = "astrocommunity.git.openingh-nvim" },
  { import = "astrocommunity.search.nvim-spectre" },
  { import = "astrocommunity.syntax.vim-easy-align" },
}
