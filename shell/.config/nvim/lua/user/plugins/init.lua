return function(plugins)
	local user_plugins = {
		{
			"catppuccin/nvim",
			as = "catppuccin",
			config = function()
				-- code
				require("catppuccin").setup({
					dim_inactive = {
						enabled = false,
						shade = "dark",
						percentage = 0.15,
					},
					compile = {
						enabled = true,
						path = vim.fn.stdpath("cache") .. "/catppuccin",
					},
					term_colors = true,
					transparent_background = true,
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
						treesitter_context = true,
						notify = true,
						gitsigns = true,
						cmp = true,
						telescope = true,
						treesitter = true,
						nvimtree = true,
						native_lsp = {
							enabled = true,
						},
					},
				})
			end,
		},
		{
			"nvim-treesitter/nvim-treesitter-textobjects",
			after = "nvim-treesitter",
		},
		{
			"kylechui/nvim-surround",
			tag = "*", -- Use for stability; omit to use `main` branch for the latest features
			opt = true,
			event = {
				"BufRead",
				"BufNewFile",
			},
			config = function()
				require("nvim-surround").setup({})
			end,
		},
		{
			"nvim-treesitter/nvim-treesitter-context",
			after = "nvim-treesitter",
			config = function()
				require("treesitter-context").setup({
					enable = true,
					trim_scope = "outer",
				})
			end,
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
			event = {
				"BufRead",
				"BufNewFile",
			},
			config = function()
				local telescope = require("telescope")
				telescope.load_extension("harpoon")
			end,
			requires = "nvim-lua/plenary.nvim",
		},
		{
			"vimpostor/vim-tpipeline",
		},
		{
			"ThePrimeagen/git-worktree.nvim",
			requires = {
				"nvim-lua/plenary.nvim",
			},
			after = {
				"telescope.nvim",
			},
			config = function()
				require("git-worktree").setup({
					autopush = true,
				})
				require("telescope").load_extension("git_worktree")
			end,
		},
		{
			"phaazon/hop.nvim",
			event = {
				"BufRead",
				"BufNewFile",
			},
			config = function()
				require("hop").setup()
			end,
		},
		{
			"nvim-telescope/telescope-media-files.nvim",
			config = function()
				local telescope = require("telescope")
				telescope.load_extension("media_files")
			end,
			after = {
				"telescope.nvim",
			},
		},
		{
			"jabirali/vim-tmux-yank",
		},
		{
			"edolphin-ydf/goimpl.nvim",
			ft = "go",
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
			ft = {
				"go",
				"python",
				"java",
			},
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
		{
			"ray-x/lsp_signature.nvim",
			after = "nvim-cmp",
			config = function()
				require("user.plugins.lsp_signature")
			end,
			requires = "hrsh7th/nvim-cmp",
		},
		{
			"mfussenegger/nvim-jdtls",
			ft = {
				"java",
			},
			requires = {
				"nvim-lspconfig",
			},
			config = function()
				require("user.plugins.nvim-jdtls")
			end,
		},
		{
			"nvim-neotest/neotest",
			opt = true,
			requires = {
				"nvim-lua/plenary.nvim",
				"nvim-treesitter/nvim-treesitter",
				"antoinemadec/FixCursorHold.nvim",
				"haydenmeade/neotest-jest",
				"nvim-neotest/neotest-go",
				"nvim-neotest/neotest-python",
			},
			module = "test",
			config = function()
				-- code
				require("user.plugins.neotest")
			end,
		},
		{
			"vuki656/package-info.nvim",
			opt = true,
			module = "package-info",
			requires = "MunifTanjim/nui.nvim",
			config = function()
				-- code
				require("package-info").setup()
			end,
		},
		{
			"f-person/git-blame.nvim",
			opt = true,
			event = {
				"BufRead",
				"BufNewFile",
			},
		},
		{
			"folke/twilight.nvim",
			opt = true,
			event = {
				"BufRead",
				"BufNewFile",
			},
			config = function()
				require("twilight").setup({
					-- your configuration comes here
					-- or leave it empty to use the default settings
					-- refer to the configuration section below
				})
			end,
		},
		{
			"Pocco81/true-zen.nvim",
			after = "twilight.nvim",
			config = function()
				-- code
				require("user.plugins.true-zen")
			end,
		},
		["ziontee113/syntax-tree-surfer"] = {
			cmd = {
				"STSSelectChildNode",
				"STSSelectCurrentNode",
				"STSSelectMasterNode",
				"STSSelectNextSiblingNode",
				"STSSelectParentNode",
				"STSSelectPrevSiblingNode",
				"STSSwapDownNormal",
				"STSSwapNextVisual",
				"STSSwapPrevVisual",
				"STSSwapUpNormal",
			},
			config = function()
				require("user.plugins.syntax-tree-surfer")
			end,
		},
		["petertriho/nvim-scrollbar"] = {
			opt = true,
			event = {
				"BufRead",
				"BufNewFile",
			},
			config = function()
				require("scrollbar").setup()
			end,
		},
		["jayp0521/mason-null-ls.nvim"] = {
			after = {
				"null-ls.nvim",
				"mason.nvim",
			},
			config = function()
				require("mason-null-ls").setup({
					automatic_installation = true,
				})
			end,
		},
		["romainl/vim-cool"] = {
			opt = true,
			event = {
				"BufRead",
				"BufNewFile",
			},
		},
		["ellisonleao/glow.nvim"] = {
			ft = "markdown",
			config = function()
				require("glow").setup({
					width = 120,
				})
			end,
		},
		["sindrets/diffview.nvim"] = {
			opt = true,
			event = {
				"BufRead",
				"BufNewFile",
			},
			requires = "nvim-lua/plenary.nvim",
			config = function()
				local actions = require("diffview.actions")

				require("diffview").setup({
					enhanced_diff_hl = true,
					keymaps = {
						view = {
							["<leader>b"] = false,
							["<leader>o"] = actions.toggle_files,
						},
					},
				})
			end,
		},
		["jayp0521/mason-nvim-dap"] = {
			after = {
				"mason.nvim",
				"nvim-dap",
			},
			config = function()
				require("mason-nvim-dap").setup({
					automatic_installation = true,
				})
			end,
		},
		["WhoIsSethDaniel/mason-tool-installer.nvim"] = {
			after = "mason.nvim",
			run = ":MasonToolsUpdate",
			config = function()
				require("mason-tool-installer").setup(require("user.plugins.mason-tool-installer"))
			end,
		},
		["andweeb/presence.nvim"] = {
			opt = true,
			config = function()
				require("presence"):setup({
					log_level = "debug",
				})
			end,
		},
	}

	return vim.tbl_deep_extend("force", plugins, user_plugins)
end
