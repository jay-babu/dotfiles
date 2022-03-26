local M = {}

local plugin_conf = require('custom.plugins.configs')
local userPlugins = require('custom.plugins')

M.options = {
	relativenumber = true,
	shiftwidth = 4,
	tabstop = 4,

	nvChad = {
		copy_del = false,
	},
}

M.plugins = {
	status = {
		colorizer = true,
		dashboard = true,
		snippets = true,
	},

	options = {
		lspconfig = {
			setup_lspconf = 'custom.plugins.lspconfig',
		},
	},

	default_plugin_config_replace = {
		nvim_treesitter = plugin_conf.treesitter,
		nvim_tree = plugin_conf.nvimtree,
		bufferline = plugin_conf.bufferline,
	},

	install = userPlugins,
}

M.ui = {
	theme = 'catppuccin',
	-- hl_override = 'custom.highlights',
	transparency = true,
}

return M