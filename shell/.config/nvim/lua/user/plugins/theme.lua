return {
	{
		"folke/tokyonight.nvim",
		opts = {
			transparent = true,
		},
	},
	{ import = "astrocommunity.colorscheme.catppuccin" },
	{
		"jay-babu/colorscheme-randomizer.nvim",
		dependencies = {
			{ "catppuccin/nvim", name = "catppuccin" },
			{ "folke/tokyonight.nvim" },
			{ "AstroNvim/astrotheme" },
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
		},
		event = "User AstroFile",
	},
}
