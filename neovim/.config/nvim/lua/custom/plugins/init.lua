return {
	{
		'TovarishFin/vim-solidity',
		ft = { 'solidity' },
	},

	{
		'jose-elias-alvarez/null-ls.nvim',
		after = 'nvim-lspconfig',
		config = function()
			require('custom.plugins.null-ls').setup()
		end,
	},

	{
		'windwp/nvim-ts-autotag',
		ft = { 'html', 'javascript', 'javascriptreact', 'typescriptreact', 'svelte', 'vue' },
		after = 'nvim-treesitter',
		config = function()
			require('nvim-ts-autotag').setup()
		end,
	},

	{
		'Pocco81/TrueZen.nvim',
		cmd = {
			'TZAtaraxis',
			'TZMinimalist',
			'TZFocus',
		},
		config = function()
			require('custom.plugins.truezen')
		end,
	},

	{
		'akinsho/toggleterm.nvim',
		cmd = {
			'ToggleTerm',
		},
		config = function()
			-- code
			require('toggleterm').setup({
				close_on_exit = true,
				direction = 'float',
				hide_numbers = true,
				open_mapping = [[<c-\>]],
				shade_filetypes = {},
				shade_terminals = true,
				size = 20,
				float_opts = {
					border = 'curved',
					winblend = 3,
					highlights = {
						border = 'Normal',
						background = 'Normal',
					},
				},
			})
		end,
	},
}
