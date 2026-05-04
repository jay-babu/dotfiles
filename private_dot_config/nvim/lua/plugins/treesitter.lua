---@type LazySpec
return {
  {
    "nvim-treesitter/nvim-treesitter",
    dependencies = {
      "nvim-treesitter/nvim-treesitter-textobjects",
      {
        "nvim-treesitter/nvim-treesitter-context",
        name = "treesitter-context",
        enabled = false,
        opts = {
          {
            enable = true,
            trim_scope = "outer",
          },
        },
      },
      {
        "stevearc/aerial.nvim",
        enabled = false,
      },
    },
  },
  {
    "AstroNvim/astrocore",
    ---@type AstroCoreOpts
    opts = function(_, opts)
      local astrocore = require "astrocore"
      opts.treesitter = opts.treesitter or {}
      opts.treesitter.highlight = true
      opts.treesitter.indent = true
      opts.treesitter.auto_install = vim.fn.executable "tree-sitter" == 1
      opts.treesitter.ensure_installed = astrocore.list_insert_unique(opts.treesitter.ensure_installed or {}, {
        "fish",
        "go",
        "graphql",
        "json",
        "kotlin",
        "lua",
        "mermaid",
        "python",
        "rust",
        "smithy",
        "typescript",
      })
      opts.treesitter.textobjects = astrocore.extend_tbl(opts.treesitter.textobjects or {}, {
        select = {
          select_textobject = {
            ["af"] = { query = "@function.outer", desc = "Around function" },
            ["if"] = { query = "@function.inner", desc = "Inside function" },
            ["ax"] = { query = "@class.outer", desc = "Around class" },
            ["ix"] = { query = "@class.inner", desc = "Inside class" },
          },
        },
        move = {
          goto_next_start = {
            ["]f"] = { query = "@function.outer", desc = "Next function start" },
            ["]x"] = { query = "@class.outer", desc = "Next class start" },
          },
          goto_next_end = {
            ["]F"] = { query = "@function.outer", desc = "Next function end" },
            ["]X"] = { query = "@class.outer", desc = "Next class end" },
          },
          goto_previous_start = {
            ["[f"] = { query = "@function.outer", desc = "Previous function start" },
            ["[x"] = { query = "@class.outer", desc = "Previous class start" },
          },
          goto_previous_end = {
            ["[F"] = { query = "@function.outer", desc = "Previous function end" },
            ["[X"] = { query = "@class.outer", desc = "Previous class end" },
          },
        },
        swap = {
          swap_next = {
            [">B"] = { query = "@block.outer", desc = "Swap next block" },
            [">F"] = { query = "@function.outer", desc = "Swap next function" },
            [">P"] = { query = "@parameter.inner", desc = "Swap next parameter" },
          },
          swap_previous = {
            ["<B"] = { query = "@block.outer", desc = "Swap previous block" },
            ["<F"] = { query = "@function.outer", desc = "Swap previous function" },
            ["<P"] = { query = "@parameter.inner", desc = "Swap previous parameter" },
          },
        },
      })
      return opts
    end,
  },
  {
    "ziontee113/syntax-tree-surfer",
    cmd = {
      "STSSelectChildNode",
      "STSSelectCurrentNode",
      "STSSelectMasterNode",
      "STSSelectNextSiblingNode",
      "STSSelectParentNode",
      "STSSelectPrevSiblingNode",
      "STSSwapDownNormal",
      "STSSwapNextVisual",
      "STSSwapPrevVisual",
      "STSSwapUpNormal",
    },
    opts = {
      highlight_group = "HopNextKey",
    },
    incremental_selection = {
      enable = true,
      keymaps = {
        init_selection = "<CR>",
        node_incremental = "<CR>",
        scope_incremental = "<S-CR>",
        node_decremental = "<BS>",
      },
    },
  },
  {
    "AstroNvim/astrolsp",
    opts = function(
      _,
      ---@type AstroLSPOpts
      opts
    )
      opts.servers = opts.servers or {}
      table.insert(opts.servers, "kotlin_lsp")
      table.insert(opts.servers, "postgres_lsp")

      -- extend our configuration table with manually configured servers
      opts.config = require("astrocore").extend_tbl(opts.config or {}, {
        kotlin_lsp = {
          cmd = { "kotlin-ls", "--stdio" },
          single_file_support = true,
          filetypes = { "kotlin" },
          root_markers = { "build.gradle", "build.gradle.kts", "pom.xml" },
        },
        postgres_lsp = {
          cmd = { "postgrestools", "lsp-proxy" },
          single_file_support = true,
          filetypes = { "sql" },
          root_markers = { "postgrestools.jsonc", ".git" },
        },
      })
    end,
  },
}
