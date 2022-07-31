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
			"williamboman/nvim-lsp-installer",
			disable = true,
		},
		{
			"williamboman/mason.nvim",
			config = function()
				require("user.plugins.mason")
			end,
		},
		-- LSP manager
		{
			"williamboman/mason-lspconfig.nvim",
			after = { "mason.nvim", "nvim-lspconfig" },
			config = function()
				require("user.plugins.mason-lspconfig")
				require("configs.lsp")
			end,
		},
		{
			"WhoIsSethDaniel/mason-tool-installer.nvim",
			after = {
				"mason.nvim",
			},
			run = ":MasonToolsUpdate",
			config = function()
				require("user.plugins.mason-tool-installer")
			end,
		},
		{
			"mfussenegger/nvim-jdtls",
			after = {
				"nvim-lspconfig",
			},
		},
	}

	return vim.tbl_deep_extend("force", plugins, user_plugins)
end
