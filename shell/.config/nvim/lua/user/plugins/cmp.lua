return {
  {
    "hrsh7th/nvim-cmp",
    dependencies = {
      "saadparwaiz1/cmp_luasnip",
      "hrsh7th/cmp-buffer",
      "hrsh7th/cmp-path",
      "hrsh7th/cmp-nvim-lsp",
      "rcarriga/cmp-dap",
    },
    event = "InsertEnter",
    opts = {
      enabled = function()
        return vim.api.nvim_get_option_value("buftype", { buf = 0 }) ~= "prompt"
            or require("cmp_dap").is_dap_buffer()
      end,
    },
    config = function(_, opts)
      require("cmp").setup(opts)
      require("cmp").setup.filetype({ "dap-repl", "dapui_watches", "dapui_hover" }, {
        sources = {
          { name = "dap" },
        },
      })
    end,
  },
}
