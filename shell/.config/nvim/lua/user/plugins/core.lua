return {
	{
		"folke/tokyonight.nvim",
		opts = {
			style = "storm",
			transparent = true,
			on_highlights = function(hl, c)
				local prompt = "#2d3149"
				hl.TelescopeNormal = {
					bg = c.bg_dark,
					fg = c.fg_dark,
				}
				hl.TelescopeBorder = {
					bg = c.bg_dark,
					fg = c.bg_dark,
				}
				hl.TelescopePromptNormal = {
					bg = prompt,
				}
				hl.TelescopePromptBorder = {
					bg = prompt,
					fg = prompt,
				}
				hl.TelescopePromptTitle = {
					bg = prompt,
					fg = prompt,
				}
				hl.TelescopePreviewTitle = {
					bg = c.bg_dark,
					fg = c.bg_dark,
				}
				hl.TelescopeResultsTitle = {
					bg = c.bg_dark,
					fg = c.bg_dark,
				}
			end,
		},
	},
	{
		"ThePrimeagen/harpoon",
		event = "User AstroFile",
		config = function()
			local telescope = require("telescope")
			telescope.load_extension("harpoon")
		end,
	},
	{
		"phaazon/hop.nvim",
		opts = {},
	},
	{
		"vuki656/package-info.nvim",
		requires = "MunifTanjim/nui.nvim",
		config = true,
		event = "BufRead package.json",
	},
}
