return astronvim.user_plugin_opts("plugins.init", {
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
		disable = true,
	},
	["folke/tokyonight.nvim"] = {
		config = function()
			require("tokyonight").setup({
				style = "storm",
				transparent = true,
				on_highlights = function(hl, c)
					local prompt = "#2d3149"
					hl.TelescopeNormal = {
						bg = c.bg_dark,
						fg = c.fg_dark,
					}
					hl.TelescopeBorder = {
						bg = c.bg_dark,
						fg = c.bg_dark,
					}
					hl.TelescopePromptNormal = {
						bg = prompt,
					}
					hl.TelescopePromptBorder = {
						bg = prompt,
						fg = prompt,
					}
					hl.TelescopePromptTitle = {
						bg = prompt,
						fg = prompt,
					}
					hl.TelescopePreviewTitle = {
						bg = c.bg_dark,

						fg = c.bg_dark,
					}
					hl.TelescopeResultsTitle = {
						bg = c.bg_dark,
						fg = c.bg_dark,
					}
				end,
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
		setup = function()
			table.insert(astronvim.file_plugins, "nvim-surround")
		end,
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
		opt = true,
		setup = function()
			table.insert(astronvim.file_plugins, "harpoon")
		end,
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
		opt = true,
		setup = function()
			table.insert(astronvim.file_plugins, "hop.nvim")
		end,
		config = function()
			require("hop").setup()
		end,
	},
	{
		"nvim-telescope/telescope-media-files.nvim",
		after = {
			"telescope.nvim",
		},
		config = function()
			local telescope = require("telescope")
			telescope.load_extension("media_files")
		end,
	},
	["nvim-telescope/telescope-file-browser.nvim"] = {
		after = "telescope.nvim",
		config = function()
			require("user.plugins.telescope-file-browser")
		end,
	},
	["nvim-telescope/telescope-hop.nvim"] = {
		after = "telescope.nvim",
		config = function()
			require("user.plugins.telescope-hop")
		end,
	},
	["nvim-telescope/telescope-project.nvim"] = {
		requires = "telescope-file-browser.nvim",
		after = "telescope.nvim",
		config = function()
			require("user.plugins.telescope-project")
		end,
	},
	{
		"jabirali/vim-tmux-yank",
		opt = true,
		setup = function()
			table.insert(astronvim.file_plugins, "vim-tmux-yank")
		end,
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
		"ray-x/lsp_signature.nvim",
		after = "nvim-cmp",
		config = function()
			require("user.plugins.lsp_signature")
		end,
		requires = "hrsh7th/nvim-cmp",
	},
	["lvimuser/lsp-inlayhints.nvim"] = {
		module = "lsp-inlayhints",
		config = function()
			require("user.plugins.lsp-inlayhints")
		end,
	},
	{
		"mfussenegger/nvim-jdtls",
		ft = {
			"java",
		},
		requires = {
			"neovim/nvim-lspconfig",
		},
		config = function()
			require("user.plugins.nvim-jdtls")
		end,
	},
	{
		"nvim-neotest/neotest",
		requires = {
			"nvim-lua/plenary.nvim",
			"nvim-treesitter/nvim-treesitter",
			"antoinemadec/FixCursorHold.nvim",
			"haydenmeade/neotest-jest",
			"nvim-neotest/neotest-go",
			"nvim-neotest/neotest-vim-test",
			"nvim-neotest/neotest-python",
		},
		module = "neotest",
		config = function()
			require("user.plugins.neotest")
		end,
	},
	["vim-test/vim-test"] = {
		after = "neotest",
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
		setup = function()
			table.insert(astronvim.file_plugins, "git-blame.nvim")
		end,
	},
	{
		"folke/twilight.nvim",
		opt = true,
		setup = function()
			table.insert(astronvim.file_plugins, "twilight.nvim")
		end,
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
		setup = function()
			table.insert(astronvim.file_plugins, "nvim-scrollbar")
		end,
		config = function()
			require("scrollbar").setup()
		end,
	},
	["romainl/vim-cool"] = {
		opt = true,
		setup = function()
			table.insert(astronvim.file_plugins, "vim-cool")
		end,
	},
	["sindrets/diffview.nvim"] = {
		opt = true,
		requires = {
			"nvim-lua/plenary.nvim",
			"nvim-tree/nvim-web-devicons",
		},
		setup = function()
			table.insert(astronvim.git_plugins, "diffview.nvim")
		end,
		config = function()
			require("user.plugins.diffview")
		end,
	},
	["theHamsta/nvim-dap-virtual-text"] = {
		requires = {
			"mfussenegger/nvim-dap",
			"nvim-treesitter/nvim-treesitter",
		},
		after = "nvim-dap",
		config = function()
			require("nvim-dap-virtual-text").setup()
		end,
	},
	["WhoIsSethDaniel/mason-tool-installer.nvim"] = {
		after = "mason.nvim",
		run = ":MasonToolsUpdate",
		config = function()
			require("mason-tool-installer").setup(require("user.plugins.mason-tool-installer"))
		end,
	},
	["jose-elias-alvarez/typescript.nvim"] = {
		after = "mason-lspconfig.nvim",
		ft = {
			"typescript",
			"typescriptreact",
			"javascript",
			"javascriptreact",
		},
		config = function()
			require("typescript").setup({
				server = astronvim.lsp.server_settings("tsserver"),
			})
		end,
	},
	["MunifTanjim/nui.nvim"] = {
		opt = false,
	},
	["ray-x/go.nvim"] = {
		after = "mason-lspconfig.nvim",
		ft = {
			"go",
		},
		config = function()
			require("user.plugins.go")
		end,
	},
	["christoomey/vim-tmux-navigator"] = {
		opt = true,
		setup = function()
			table.insert(astronvim.file_plugins, "vim-tmux-navigator")
		end,
	},
}, nil, "work")
