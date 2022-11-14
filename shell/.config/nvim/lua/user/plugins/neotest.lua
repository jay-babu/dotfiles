require("neotest").setup({
	adapters = {
		require("neotest-python")({
			-- Extra arguments for nvim-dap configuration
			dap = { justMyCode = false },
		}),
		require("neotest-go"),
		require("neotest-vim-test")({ allow_file_types = { "java" } }),
		require("neotest-jest")({
			jestCommand = "npm test --",
			env = { CI = true },
			cwd = function(path)
				return vim.fn.getcwd()
			end,
		}),
	},
})
