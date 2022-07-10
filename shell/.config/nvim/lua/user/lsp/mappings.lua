return {
	n = {
		["gr"] = {
			function()
				vim.lsp.buf.references({
					includeDeclaration = false,
				})
			end,
			desc = "References of current symbol",
		},
	},
}
