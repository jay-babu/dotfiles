-- AstroCommunity: import any community modules here
-- We import this file in `lazy_setup.lua` before the `plugins/` folder.
-- This guarantees that the specs are processed before any user plugins.

---@type LazySpec
return {
  { "AstroNvim/astrocommunity" },
  { import = "astrocommunity.pack.lua" },
  { import = "astrocommunity.pack.full-dadbod" },
  { import = "astrocommunity.quickfix.nvim-bqf" },
  { import = "astrocommunity.debugging.persistent-breakpoints-nvim" },
  { import = "astrocommunity.debugging.nvim-dap-repl-highlights" },
  { import = "astrocommunity.markdown-and-latex.render-markdown-nvim" },
  { import = "astrocommunity.editing-support.undotree" },
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
      opts.exclude = vim.iter({ opts.exclude or {}, { "vx", "vX", "xx", "xX", "vc", "cc", "C" } }):flatten():totable()
    end,
  },
  { import = "astrocommunity.editing-support.dial-nvim" },
  { import = "astrocommunity.editing-support.nvim-regexplainer" },
  { import = "astrocommunity.editing-support.treesj" },
  {
    "Wansmer/treesj",
    optional = true,
    opts = { max_join_length = 9999 },
  },
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
    optional = true,
    event = function(_, _) return {} end,
  },
  { import = "astrocommunity.test.neotest" },
  { import = "astrocommunity.pack.json" },
  { import = "astrocommunity.pack.lua" },
  { import = "astrocommunity.pack.markdown" },
  { import = "astrocommunity.pack.python-ruff" },
  { import = "astrocommunity.pack.typescript" },
  { import = "astrocommunity.git.git-blame-nvim" },
  { import = "astrocommunity.pack.rust" },
  { import = "astrocommunity.pack.yaml" },
  { import = "astrocommunity.pack.bash" },
  { import = "astrocommunity.pack.templ" },
  { import = "astrocommunity.fuzzy-finder.fzf-lua" },
  { import = "astrocommunity.terminal-integration.vim-tmux-yank" },
  { import = "astrocommunity.syntax.vim-cool" },
  { import = "astrocommunity.editing-support.rainbow-delimiters-nvim" },
  { import = "astrocommunity.motion.nvim-spider" },
  { import = "astrocommunity.recipes.neovide" },
  { import = "astrocommunity.media.vim-wakatime" },
  { import = "astrocommunity.editing-support.nvim-regexplainer" },
  {
    "HiPhish/rainbow-delimiters.nvim",
    event = "VeryLazy",
    optional = true,
  },
  { import = "astrocommunity.editing-support.conform-nvim" },
  {
    "jay-babu/mason-null-ls.nvim",
    optional = true,
    opts = {
      handlers = {
        clang_format = function() end,
      },
    },
  },
  { import = "astrocommunity.completion.avante-nvim" },
  { import = "astrocommunity.completion.blink-cmp" },
  { import = "astrocommunity.completion.copilot-lua-cmp" },
  { import = "astrocommunity.editing-support.copilotchat-nvim" },
  { -- optional saghen/blink.cmp completion source
    "saghen/blink.cmp",
    optional = true,
    dependencies = {
      {
        "kristijanhusak/vim-dadbod-completion",
      },
      {
        "kristijanhusak/vim-dadbod-ui",
      },
    },
    build = "cargo build --release",

    ---@type blink.cmp.Config
    opts = {
      sources = {
        -- add vim-dadbod-completion to your completion providers
        default = { "dadbod" },
        providers = {
          dadbod = { name = "Dadbod", module = "vim_dadbod_completion.blink" },
        },
      },
      appearance = {
        -- Blink does not expose its default kind icons so you must copy them all (or set your custom ones) and add Copilot
        kind_icons = {
          Copilot = "",
          Text = "󰉿",
          Method = "󰊕",
          Function = "󰊕",
          Constructor = "󰒓",

          Field = "󰜢",
          Variable = "󰆦",
          Property = "󰖷",

          Class = "󱡠",
          Interface = "󱡠",
          Struct = "󱡠",
          Module = "󰅩",

          Unit = "󰪚",
          Value = "󰦨",
          Enum = "󰦨",
          EnumMember = "󰦨",

          Keyword = "󰻾",
          Constant = "󰏿",

          Snippet = "󱄽",
          Color = "󰏘",
          File = "󰈔",
          Reference = "󰬲",
          Folder = "󰉋",
          Event = "󱐋",
          Operator = "󰪚",
          TypeParameter = "󰬛",
        },
      },
    },
  },
  { import = "astrocommunity.code-runner.overseer-nvim" },
  { import = "astrocommunity.recipes.vscode" },
  { import = "astrocommunity.git.gist-nvim" },
  { import = "astrocommunity.git.openingh-nvim" },
  { import = "astrocommunity.search.nvim-spectre" },
  { import = "astrocommunity.syntax.vim-easy-align" },
  { import = "astrocommunity.git.diffview-nvim" },
}
