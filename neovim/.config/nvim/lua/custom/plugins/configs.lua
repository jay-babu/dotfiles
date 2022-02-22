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

return M
