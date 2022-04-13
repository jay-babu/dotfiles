return {
	{
		"TovarishFin/vim-solidity",
		ft = { "solidity" },
	},

	{
		"jose-elias-alvarez/null-ls.nvim",
		after = "nvim-lspconfig",
		config = function()
			require("custom.plugins.null-ls").setup()
		end,
	},

	{
		"windwp/nvim-ts-autotag",
		ft = { "html", "javascript", "javascriptreact", "typescriptreact", "svelte", "vue" },
		after = "nvim-treesitter",
		config = function()
			require("nvim-ts-autotag").setup()
		end,
	},

	{
		"Pocco81/TrueZen.nvim",
		cmd = {
			"TZAtaraxis",
			"TZMinimalist",
			"TZFocus",
		},
		config = function()
			require("custom.plugins.truezen")
		end,
	},

	{
		"p00f/nvim-ts-rainbow",
		after = "nvim-treesitter",
	},
	{
		"github/copilot.vim",
	},
}
