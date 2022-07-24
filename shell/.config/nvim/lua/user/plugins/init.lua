return function(plugins)
	local user_plugins = {
		{
			"catppuccin/nvim",
			as = "catppuccin",
			config = function()
				-- code
				require("catppuccin").setup({
					dim_inactive = {
						enabled = true,
						shade = "dark",
						percentage = 0.15,
					},
					compile = {
						enabled = true,
						path = vim.fn.stdpath("cache") .. "/catppuccin",
					},
					term_colors = true,
					integrations = {
						neotree = {
							enabled = true,
							show_root = false,
							transparent_panel = true,
						},
						hop = true,
						ts_rainbow = true,
						which_key = true,
						dap = {
							enabled = true,
							enable_ui = true,
						},
						aerial = true,
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
		{
			"jabirali/vim-tmux-yank",
		},
		{
			"edolphin-ydf/goimpl.nvim",
			requires = {
				{ "nvim-lua/plenary.nvim" },
				{ "nvim-lua/popup.nvim" },
				{ "nvim-telescope/telescope.nvim" },
				{ "nvim-treesitter/nvim-treesitter" },
			},
			config = function()
				require("telescope").load_extension("goimpl")
			end,
		},
		{
			"mfussenegger/nvim-dap",
			module = "dap",
			config = function()
				require("user.plugins.dap")
			end,
		},
		{
			"rcarriga/nvim-dap-ui",
			after = "nvim-dap",
			config = function()
				require("user.plugins.nvim-dap-ui")
			end,
			requires = { "mfussenegger/nvim-dap" },
		},
	}

	return vim.tbl_deep_extend("force", plugins, user_plugins)
end
