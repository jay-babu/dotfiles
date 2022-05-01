return {
	ensure_installed = {
		"bash",
		"cpp",
		"css",
		"dockerfile",
		"go",
		"graphql",
		"html",
		"http",
		"javascript",
		"json",
		"lua",
		"make",
		"markdown",
		"python",
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
