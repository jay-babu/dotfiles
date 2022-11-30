require("go").setup(astronvim.user_plugin_opts("plugins.go", {
  lsp_cfg = astronvim.lsp.server_settings("gopls"),
  lsp_on_attach = astronvim.lsp.on_attach,
  lsp_keymaps = false,
  lsp_inlay_hints = { enable = false },
}, nil, "work"))
