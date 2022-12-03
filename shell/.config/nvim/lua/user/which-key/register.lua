return {
	n = {
		["<leader>"] = {
			y = {
				function()
					vim.cmd([[:%y]])
				end,
				"Yank file to clipboard",
			},
			n = {
				name = "package.json",
				i = {
					function()
						require("package-info").install()
					end,
					"Install a new dependency",
				},
				d = {
					function()
						require("package-info").delete()
					end,
					"Delete dependency on line",
				},
			},
			z = {
				f = {
					function()
						require("true-zen").focus()
					end,
					"True Zen Focus",
				},
				m = {
					function()
						require("true-zen").minimalist()
					end,
					"True Zen Minimalist",
				},
				a = {
					function()
						require("true-zen").ataraxis()
					end,
					"True Zen Ataraxis",
				},
			},
			s = {
				name = "Surf",
				s = { "<cmd>STSSelectMasterNode<cr>", "Surf" },
				S = { "<cmd>STSSelectCurrentNode<cr>", "Surf Node" },
			},
		},
	},
	v = {},
}
