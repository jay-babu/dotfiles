return {
  tsserver = function(_, opts)
    require("typescript").setup({ server = opts })
  end,
  gopls = function(_, opts)
    require("go").setup({
      lsp_cfg = opts,
      lsp_on_attach = astronvim.lsp.on_attach,
      lsp_keymaps = false,
      lsp_inlay_hints = { enable = false },
    })
  end,
  jdtls = function(_, _) end,
}
