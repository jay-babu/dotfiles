return astronvim.user_opts("work.lsp.setup_handlers", {
	tsserver = function(_, opts)
		require("typescript").setup({ server = opts })
	end,
	gopls = function(_, opts)
		require("go").setup({
			lsp_cfg = opts,
			lsp_on_attach = require("astronvim.utils.lsp").on_attach,
			lsp_keymaps = false,
			lsp_inlay_hints = { enable = false },
		})
	end,
})
