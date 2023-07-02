return {
	{ "AstroNvim/astrocommunity", version = "*" },
	{ import = "astrocommunity.bars-and-lines.heirline-vscode-winbar" },
	{ import = "astrocommunity.debugging.nvim-bqf" },
	{ import = "astrocommunity.debugging.persistent-breakpoints-nvim" },
	{ import = "astrocommunity.diagnostics.trouble-nvim" },
	{
		import = "astrocommunity.editing-support.cutlass-nvim",
	},
	{
		"gbprod/cutlass.nvim",
		opts = function(_, opts)
			opts.exclude = vim.tbl_flatten({ opts.exclude or {}, { "vx", "vX", "xx", "xX" } })
		end,
	},
	{ import = "astrocommunity.editing-support.dial-nvim" },
	{ import = "astrocommunity.editing-support.nvim-regexplainer" },
	{ import = "astrocommunity.editing-support.refactoring-nvim" },
	{
		import = "astrocommunity.editing-support.treesj",
		opts = { max_join_length = 240 },
	},
	{ import = "astrocommunity.indent.indent-blankline-nvim" },
	{ import = "astrocommunity.indent.mini-indentscope" },
	{ import = "astrocommunity.motion.harpoon" },
	{ import = "astrocommunity.motion.hop-nvim" },
	{ import = "astrocommunity.motion.nvim-surround" },
	{ import = "astrocommunity.motion.vim-matchup" },
	{ import = "astrocommunity.project.neoconf-nvim" },
	{ import = "astrocommunity.scrolling.nvim-scrollbar" },
	{ import = "astrocommunity.utility.noice-nvim" },
	-- {
	-- 	import = "astrocommunity.utility.transparent-nvim",
	-- 	config = function(_, opts)
	-- 		require("transparent").setup(opts)
	-- 		vim.cmd([[TransparentEnable]])
	-- 	end,
	-- },
	{ import = "astrocommunity.pack.docker" },
	{ import = "astrocommunity.pack.go" },
	{ import = "astrocommunity.pack.json" },
	{ import = "astrocommunity.pack.lua" },
	{ import = "astrocommunity.pack.markdown" },
	{ import = "astrocommunity.pack.python" },
	{ import = "astrocommunity.pack.typescript" },
	{ import = "astrocommunity.git.git-blame-nvim" },
	{ import = "astrocommunity.pack.rust" },
	{ import = "astrocommunity.pack.yaml" },
	{ import = "astrocommunity.pack.bash" },
	{ import = "astrocommunity.terminal-integration.vim-tmux-yank" },
	-- { import = "astrocommunity.terminal-integration.vim-tpipeline" },
	{ import = "astrocommunity.syntax.vim-cool" },
	{ import = "astrocommunity.lsp.lsp-inlayhints-nvim" },
}
