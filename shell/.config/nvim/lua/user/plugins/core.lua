return {
	{
		"catppuccin/nvim",
		name = "catppuccin",
		opts = {
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
		},
		enabled = false,
	},
	{
		"folke/tokyonight.nvim",
		opts = {
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
		},
	},
	{
		"kylechui/nvim-surround",
		version = "*", -- Use for stability; omit to use `main` branch for the latest features
		event = "User AstroFile",
		opts = {},
		config = function(_, opts)
			require("nvim-surround").setup(opts)
		end,
	},
	{
		"ThePrimeagen/harpoon",
		event = "User AstroFile",
		config = function()
			local telescope = require("telescope")
			telescope.load_extension("harpoon")
		end,
	},
	{
		"vimpostor/vim-tpipeline",
		lazy = false,
		enabled = false,
	},
	{
		"phaazon/hop.nvim",
		opts = {},
	},
	{
		"jabirali/vim-tmux-yank",
		event = "User AstroFile",
	},
	{
		"vuki656/package-info.nvim",
		config = function()
			require("package-info").setup()
		end,
	},
	{
		"f-person/git-blame.nvim",
		event = "User AstroFile",
	},
	{
		"folke/twilight.nvim",
		event = "User AstroFile",
		opts = {},
	},
	{
		"petertriho/nvim-scrollbar",
		opts = {},
		event = "User AstroFile",
	},
	{
		"romainl/vim-cool",
		event = "User AstroFile",
	},
	{
		"monaqa/dial.nvim",
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
}
