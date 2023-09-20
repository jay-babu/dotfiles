local utils = require("astronvim.utils")

return {
	{
		"williamboman/mason-lspconfig.nvim",
		opts = function(_, opts)
			opts.ensure_installed = utils.list_insert_unique(opts.ensure_installed, "spectral")
		end,
	},
	{
		"vinnymeller/swagger-preview.nvim",
		cmd = { "SwaggerPreview", "SwaggerPreviewStop", "SwaggerPreviewToggle" },
		opts = {
			port = 9000,
		},
	},
}
