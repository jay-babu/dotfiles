return function(plugins)
	local user_plugins = {
		{
			"catppuccin/nvim",
			as = "catppuccin",
			config = function()
				-- code
				require("catppuccin").setup({
					integrations = {
						neotree = {
							enabled = true,
							show_root = false,
							transparent_panel = true,
						},
						hop = true,
						ts_rainbow = true,
						which_key = true,
					},
				})
			end,
		},
		{
			"nvim-treesitter/nvim-treesitter-textobjects",
			after = "nvim-treesitter",
		},

		{
			"andymass/vim-matchup",
			after = "nvim-treesitter",
		},
		{
			"dstein64/vim-startuptime",
		},
		{
			"ThePrimeagen/harpoon",
			requires = "nvim-lua/plenary.nvim",
		},
		{
			"vimpostor/vim-tpipeline",
		},
		{
			"ThePrimeagen/git-worktree.nvim",
			requires = {
				"nvim-lua/plenary.nvim",
				"nvim-telescope/telescope.nvim",
			},
			config = function()
				require("git-worktree").setup({
					autopush = true,
				})
			end,
		},
		{
			"phaazon/hop.nvim",
			-- cmd = {
			-- 	"HopWord",
			-- 	"HopPattern",
			-- 	"HopChar1",
			-- 	"HopChar2",
			-- 	"HopLine",
			-- },
			config = function()
				require("hop").setup()
			end,
		},
		{
			"nvim-telescope/telescope-media-files.nvim",
			requires = {
				"nvim-telescope/telescope.nvim",
			},
		},
	}

	return vim.tbl_deep_extend("force", plugins, user_plugins)
end
