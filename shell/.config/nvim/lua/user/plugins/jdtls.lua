return {
	{
		import = "astrocommunity.editing-support.refactoring-nvim",
	},
	{
		"ThePrimeagen/refactoring.nvim",
		keys = {
			{
				"<leader>re",
				function()
					require("refactoring").refactor("Extract Function")
				end,
				{ silent = true, expr = false },
				mode = {
					"v",
					"x",
				},
				desc = "Extract Function",
			},
			{
				"<leader>rv",
				function()
					require("refactoring").refactor("Extract Variable")
				end,
				{ silent = true, expr = false },
				mode = {
					"v",
					"x",
				},
				desc = "Extract Variable",
			},
		},
	},
	{ import = "astrocommunity.pack.java" },
}
