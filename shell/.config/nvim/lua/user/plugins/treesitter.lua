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
			"kotlin",
			"lua",
			"make",
			"markdown",
			"python",
			"rust",
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
	-- vim.opt.foldmethod = "expr"
	-- vim.opt.foldexpr = "nvim_treesitter#foldexpr()"
	-- vim.opt.foldlevelstart = 99
	-- vim.opt.foldnestmax = 3
	-- vim.opt.foldminlines = 1
	-- vim.o.foldtext =
	-- 	[[substitute(getline(v:foldstart),'\\t',repeat('\ ',&tabstop),'g').'...'.trim(getline(v:foldend)) . ' (' . (v:foldend - v:foldstart + 1) . ' lines)']]
	-- https://www.reddit.com/r/neovim/comments/psl8rq/sexy_folds/
	-- vim.o.foldnestmax = 3
	-- vim.o.foldlevel = 0
	-- vim.o.foldexpr = "nvim_treesitter#foldexpr()"
	-- vim.o.foldmethod = "expr"
	-- vim.o.foldtext =
	-- 	[[substitute(getline(v:foldstart),'\\t',repeat('\ ',&tabstop),'g').'...'.trim(getline(v:foldend)) . ' (' . (v:foldend - v:foldstart + 1) . ' lines)']]
	return vim.tbl_deep_extend("force", default, overrides)
end
