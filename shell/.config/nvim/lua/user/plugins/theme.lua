return {
	{
		"folke/tokyonight.nvim",
		opts = {
			transparent = true,
		},
	},
	{ import = "astrocommunity.colorscheme.catppuccin" },
	{ import = "astrocommunity.colorscheme.monokai-pro-nvim", opts = { transparent_background = true } },
	{ import = "astrocommunity.colorscheme.nightfox-nvim", opts = { options = { transparent = true } } },
	{
		"jay-babu/colorscheme-randomizer.nvim",
		dependencies = {
			{ "catppuccin/nvim", name = "catppuccin" },
			{ "folke/tokyonight.nvim" },
			{ "AstroNvim/astrotheme" },
			{ "loctvl842/monokai-pro.nvim", opts = { transparent_background = true } },
			{ "EdenEast/nightfox.nvim", opts = { options = { transparent = true } } },
		},
		opts = {
			apply_scheme = true,
			plugin_strategy = "lazy",
			-- plugins = {
			-- 	"tokyonight.nvim",
			-- 	"catppuccin",
			-- },
			-- colorschemes = {
			-- 	"catppuccin-frappe",
			-- },
			exclude_colorschemes = {
				"tokyonight-day",
				"astrolight",
				"catppuccin-latte",
				"dawnfox",
				"dayfox",
			},
		},
		event = "User AstroFile",
	},
}
