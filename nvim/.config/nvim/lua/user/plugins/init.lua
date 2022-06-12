return function(plugins)
	local user_plugins = {
		{
			"catppuccin/nvim",
			as = "catppuccin",
			config = function()
				-- code
				require("catppuccin").setup({
					integrations = {
						neotree = {
							enabled = true,
							show_root = false,
							transparent_panel = true,
						},
						hop = true,
						ts_rainbow = true,
						which_key = true,
					},
				})
			end,
		},
		{
			"nvim-treesitter/nvim-treesitter-textobjects",
			after = "nvim-treesitter",
		},

		{
			"andymass/vim-matchup",
			after = "nvim-treesitter",
		},
		{
			"dstein64/vim-startuptime",
		},
	}

	return vim.tbl_deep_extend("force", plugins, user_plugins)
end
