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
					if vim.o.filetype == "java" then
						require("jdtls").extract_method(true)
					else
						require("refactoring").refactor("Extract Function")
					end
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
					if vim.o.filetype == "java" then
						require("jdtls").extract_variable(true)
					else
						require("refactoring").refactor("Extract Variable")
					end
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
