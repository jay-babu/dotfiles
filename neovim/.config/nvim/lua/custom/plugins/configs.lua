local M = {}

M.treesitter = {
	ensure_installed = {
		"c",
		"css",
		"dockerfile",
		"go",
		"graphql",
		"html",
		"javascript",
		"json",
		"lua",
		"python",
		"toml",
		"tsx",
		"typescript",
		"vim",
	},
	rainbow = {
		enable = true,
		extended_mode = true,
		max_file_lines = nil,
	},
}

M.nvimtree = {
	git = {
		enable = true,
	},
}

M.bufferline = {
	options = {
		diagnostics = "nvim_lsp",
	},
}

M.telescope = {
	defaults = {
		vimgrep_arguments = {
			"rg",
			"--color=never",
			"--no-heading",
			"--with-filename",
			"--line-number",
			"--column",
			"--smart-case",
			"--hidden",
			"--follow",
		},
	},
	pickers = {
		find_files = {
			hidden = true,
			file_ignore_patterns = { "^.git/" },
			follow = true,
		},
		buffers = {
			show_all_buffers = true,
			sort_lastused = true,
			mappings = {
				i = {
					["<C-d>"] = "delete_buffer",
				},
			},
		},
	},
}

return M
