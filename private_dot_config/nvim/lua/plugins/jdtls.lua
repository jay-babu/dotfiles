return {
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
      opts.ensure_installed = vim.tbl_filter(function(server) return server ~= "lemminx" end, opts.ensure_installed)
    end,
  },
  {
    "WhoIsSethDaniel/mason-tool-installer.nvim",
    optional = true,
    opts = function(_, opts)
      -- filter out the kotlin_language_server if it is already installed
      opts.ensure_installed = vim.tbl_filter(
        function(server) return server ~= "kotlin-language-server" end,
        opts.ensure_installed
      )

      opts.ensure_installed = vim.tbl_filter(function(server) return server ~= "lemminx" end, opts.ensure_installed)
    end,
  },
}
