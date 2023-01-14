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
		"phaazon/hop.nvim",
		opt = true,
		setup = function()
			table.insert(astronvim.file_plugins, "hop.nvim")
		end,
		config = function()
			require("hop").setup()
		end,
		module = "hop",
	},
	{
		"jabirali/vim-tmux-yank",
		opt = true,
		setup = function()
			table.insert(astronvim.file_plugins, "vim-tmux-yank")
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
	["MunifTanjim/nui.nvim"] = {
		opt = false,
	},
	["monaqa/dial.nvim"] = {
		module = "dial",
		config = function()
			local augend = require("dial.augend")
			require("dial.config").augends:register_group({
				default = {
					augend.integer.alias.decimal,
					augend.integer.alias.hex,
					augend.date.alias["%Y/%m/%d"],
					augend.constant.alias.bool,
					augend.semver.alias.semver,
					augend.case.new({
						types = { "camelCase", "PascalCase", "snake_case", "SCREAMING_SNAKE_CASE" },
					}),
				},
			})
		end,
	},
	["rebelot/heirline.nvim"] = {
		commit = "556666aabb57c227cbb14a996b30b2934e5ff7b1",
	},
}, nil, "work")
