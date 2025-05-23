return {
  {
    import = "astrocommunity.editing-support.refactoring-nvim",
  },
  {
    "ThePrimeagen/refactoring.nvim",
    keys = {
      {
        "<leader>re",
        function() require("refactoring").refactor "Extract Function" end,
        { silent = true, expr = false },
        mode = {
          "v",
          "x",
        },
        desc = "Extract Function",
      },
      {
        "<leader>rv",
        function() require("refactoring").refactor "Extract Variable" end,
        { silent = true, expr = false },
        mode = {
          "v",
          "x",
        },
        desc = "Extract Variable",
      },
    },
  },
  { import = "astrocommunity.pack.java" },
  {
    import = "astrocommunity.pack.kotlin",
  },
  {
    "williamboman/mason-lspconfig.nvim",
    optional = true,
    opts = function(_, opts)
      -- filter out the kotlin_language_server if it is already installed
      opts.ensure_installed = vim.tbl_filter(
        function(server) return server ~= "kotlin_language_server" end,
        opts.ensure_installed
      )
    end,
  },
  {
    "WhoIsSethDaniel/mason-tool-installer.nvim",
    optional = true,
    opts = function(_, opts)
      -- filter out the kotlin_language_server if it is already installed
      opts.ensure_installed = vim.tbl_filter(
        function(server) return server ~= "kotlin_language_server" end,
        opts.ensure_installed
      )
    end,
  },
}
