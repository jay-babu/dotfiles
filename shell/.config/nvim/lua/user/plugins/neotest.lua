return {
	"nvim-neotest/neotest",
	dependencies = {
		"nvim-lua/plenary.nvim",
		"nvim-treesitter/nvim-treesitter",
		"antoinemadec/FixCursorHold.nvim",
		"haydenmeade/neotest-jest",
		"nvim-neotest/neotest-go",
		"nvim-neotest/neotest-vim-test",
		"nvim-neotest/neotest-python",
		"vim-test/vim-test",
	},
	config = function()
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
	end,
}
