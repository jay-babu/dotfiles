-- *Must* be *S*olidity not solidity
-- require("nvim-treesitter.parsers").get_parser_configs().Solidity = {

-- 	install_info = {
-- 		url = "https://github.com/JoranHonig/tree-sitter-solidity",
-- 		files = { "src/parser.c" },
-- 		requires_generate_from_grammar = true,
-- 	},
-- 	filetype = "solidity",
-- }

return function(default)
	local overrides = {
		ensure_installed = {
			"bash",
			"cpp",
			"css",
			"dockerfile",
			"go",
			"graphql",
			"html",
			"http",
			"java",
			"javascript",
			"json",
			"lua",
			"make",
			"markdown",
			"python",
			-- "Solidity",
			"solidity",
			"toml",
			"tsx",
			"typescript",
			"vim",
			"yaml",
		},
		rainbow = {
			enable = true,
			extended_mode = true,
			max_file_lines = nil,
		},
		matchup = {
			enable = true,
		},
		textobjects = {
			select = {
				enable = true,
				lookahead = true,
				keymaps = {
					["af"] = "@function.outer",
					["if"] = "@function.inner",
					["ax"] = "@class.outer",
					["ix"] = "@class.inner",
				},
			},
			move = {
				enable = true,
				set_jumps = true,
				goto_next_start = {
					["]f"] = "@function.outer",
					["]x"] = "@class.outer",
				},
				goto_next_end = {
					["]F"] = "@function.outer",
					["]X"] = "@class.outer",
				},
				goto_previous_start = {
					["[f"] = "@function.outer",
					["[x"] = "@class.outer",
				},
				goto_previous_end = {
					["[F"] = "@function.outer",
					["[X"] = "@class.outer",
				},
			},
			swap = {
				enable = false,
			},
		},
	}
	-- vim.opt.foldmethod = expr
	-- vim.opt.foldexpr = nvim_treesitter#foldexpr()

	return vim.tbl_deep_extend("force", default, overrides)
end
