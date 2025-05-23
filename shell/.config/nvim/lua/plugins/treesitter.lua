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
    opts = function(_, opts)
      -- add more things to the ensure_installed table protecting against community packs modifying it
      opts.auto_install = vim.fn.executable "tree-sitter" == 1
      opts.ensure_installed = require("astrocore").list_insert_unique(opts.ensure_installed, {
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
        -- add more arguments for adding more treesitter parsers
      })
      opts.textobjects = {
        select = {
          enable = true,
          lookahead = true,
          keymaps = {
            ["af"] = "@function.outer",
            ["if"] = "@function.inner",
            ["ax"] = "@class.outer",
            ["ix"] = "@class.inner",
          },
        },
        move = {
          enable = true,
          set_jumps = true,
          goto_next_start = {
            ["]f"] = "@function.outer",
            ["]x"] = "@class.outer",
          },
          goto_next_end = {
            ["]F"] = "@function.outer",
            ["]X"] = "@class.outer",
          },
          goto_previous_start = {
            ["[f"] = "@function.outer",
            ["[x"] = "@class.outer",
          },
          goto_previous_end = {
            ["[F"] = "@function.outer",
            ["[X"] = "@class.outer",
          },
        },
        swap = {
          enable = true,
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
        lsp_interop = {
          enable = true,
          border = "single",
          peek_definition_code = {
            ["<leader>lp"] = { query = "@function.outer", desc = "Peek function definition" },
            ["<leader>lP"] = { query = "@class.outer", desc = "Peek class definition" },
          },
        },
      }
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

      -- extend our configuration table to have our new prolog server
      opts.config = require("astrocore").extend_tbl(opts.config or {}, {
        -- this must be a function to get access to the `lspconfig` module
        kotlin_lsp = {
          cmd = { "kotlin-ls", "--stdio" },
          single_file_support = true,
          filetypes = { "kotlin" },
          root_markers = { "build.gradle", "build.gradle.kts", "pom.xml" },
        },
      })
    end,
  },
}
