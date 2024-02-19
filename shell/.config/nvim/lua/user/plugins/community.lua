local function removeFirstLeaderFromArray(inputArray)
	local resultArray = {}

	for _, str in ipairs(inputArray) do
		local replacedString, _, count = string.gsub(str[1], "<leader>", "", 1)
		table.insert(resultArray, str)
	end
	return resultArray
end

return {
	{ "AstroNvim/astrocommunity" },
	{ import = "astrocommunity.bars-and-lines.heirline-vscode-winbar" },
	{ import = "astrocommunity.debugging.nvim-bqf" },
	{ import = "astrocommunity.debugging.persistent-breakpoints-nvim" },
	{ import = "astrocommunity.debugging.nvim-dap-repl-highlights" },
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
	{
		import = "astrocommunity.editing-support.treesj",
	},
	{
		"Wansmer/treesj",
		keys = { { "<leader><leader>m", "<CMD>TSJToggle<CR>", desc = "Toggle Treesitter Join" } },
	},
	{
		"Wansmer/treesj",
		opts = { max_join_length = 9999 },
	},
	{ import = "astrocommunity.indent.indent-blankline-nvim" },
	{ import = "astrocommunity.indent.mini-indentscope" },
	{ import = "astrocommunity.motion.harpoon" },
	{
		"ThePrimeagen/harpoon",
		keys = function(_, keys)
			return removeFirstLeaderFromArray(keys)
		end,
	},
	{ import = "astrocommunity.motion.hop-nvim" },
	{ import = "astrocommunity.motion.nvim-surround" },
	{ import = "astrocommunity.motion.vim-matchup" },
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
	{
		"ray-x/go.nvim",
		event = function(_, _)
			return {}
		end,
	},
	{ import = "astrocommunity.pack.json" },
	{ import = "astrocommunity.pack.lua" },
	{ import = "astrocommunity.pack.markdown" },
	{ import = "astrocommunity.pack.python-ruff" },
	{ import = "astrocommunity.pack.typescript" },
	{ import = "astrocommunity.git.git-blame-nvim" },
	{ import = "astrocommunity.pack.rust" },
	{ import = "astrocommunity.pack.yaml" },
	{ import = "astrocommunity.pack.bash" },
	{ import = "astrocommunity.file-explorer.oil-nvim" },
	{ import = "astrocommunity.terminal-integration.vim-tmux-yank" },
	{ import = "astrocommunity.syntax.vim-cool" },
	{ import = "astrocommunity.lsp.lsp-inlayhints-nvim" },
	{ import = "astrocommunity.editing-support.rainbow-delimiters-nvim" },
	{ import = "astrocommunity.motion.nvim-spider" },
	{ import = "astrocommunity.media.vim-wakatime" },
	{ import = "astrocommunity.editing-support.nvim-regexplainer" },
	{
		"HiPhish/rainbow-delimiters.nvim",
		event = "VeryLazy",
		optional = true,
	},
	{ import = "astrocommunity.editing-support.true-zen-nvim" },
	{
		"jay-babu/mason-null-ls.nvim",
		opts = {
			handlers = {
				clang_format = function() end,
			},
		},
	},
	{ import = "astrocommunity.completion.copilot-lua-cmp" },
	{ import = "astrocommunity.code-runner.overseer-nvim" },
}
