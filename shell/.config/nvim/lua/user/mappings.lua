return function(default)
	default.n["<S-h>"] = default.n["[b"]
	default.n["<S-l>"] = default.n["]b"]
	default.n["[b"] = nil
	default.n["]b"] = nil
	return astronvim.user_opts(
		"work.mappings",
		astronvim.extend_tbl(default, {
			n = {
				["<C-\\>"] = { "<cmd>ToggleTerm<cr>", desc = "Toggle terminal" },
				["<C-Down>"] = false,
				["<C-Left>"] = false,
				["<C-Right>"] = false,
				["<C-Up>"] = false,
				["<C-s>"] = false,
				["<C-a>"] = {
					function()
						require("dial.map").inc_normal()
					end,
				},
				["<C-x>"] = {
					function()
						require("dial.map").dec_normal()
					end,
				},
				-- resize with arrows
				["<Up>"] = {
					function()
						require("smart-splits").resize_up(2)
					end,
					desc = "Resize split up",
				},
				["<Down>"] = {
					function()
						require("smart-splits").resize_down(2)
					end,
					desc = "Resize split down",
				},
				["<Left>"] = {
					function()
						require("smart-splits").resize_left(2)
					end,
					desc = "Resize split left",
				},
				["<Right>"] = {
					function()
						require("smart-splits").resize_right(2)
					end,
					desc = "Resize split right",
				},
				["<leader>a"] = {
					function()
						require("harpoon.mark").add_file()
					end,
					desc = "Add File Harpoon",
				},
				["<leader>Y"] = {
					function()
						vim.cmd([[:%y]])
					end,
					desc = "Yank file to clipboard",
				},
				["<leader>ni"] = {
					function()
						require("package-info").install()
					end,
					desc = "Install a new dependency",
				},
				["<leader>nd"] = {
					function()
						require("package-info").delete()
					end,
					desc = "Delete a dependency",
				},
				["<leader>zf"] = {
					function()
						require("true-zen").focus()
					end,
					desc = "True Zen Focus",
				},
				["<leader>zm"] = {
					function()
						require("true-zen").minimalist()
					end,
					desc = "True Zen Minimalist",
				},
				["<leader>za"] = {
					function()
						require("true-zen").ataraxis()
					end,
					desc = "True Zen Ataraxis",
				},
				["s"] = {
					function()
						require("hop").hint_words()
					end,
				},
				["<c-e>"] = {
					function()
						require("harpoon.ui").toggle_quick_menu()
					end,
					desc = "View Harpoon Marks",
				},
				["<c-t>"] = {
					function()
						require("harpoon.ui").nav_prev()
					end,
					desc = "Harpoon Marks Previous",
				},
				["<c-s>"] = {
					function()
						require("harpoon.ui").nav_next()
					end,
					desc = "Harpoon Marks Next",
				},
				["<S-s>"] = {
					"<cmd>lua require('hop').hint_lines()<cr>",
				},
				-- Treesitter Surfer
				["<a-down>"] = {
					function()
						require("syntax-tree-surfer").move("n", false)
						vim.cmd(vim.api.nvim_replace_termcodes("normal zz", true, true, true))
					end,
					desc = "Swap next tree-sitter object",
				},
				["<a-right>"] = {
					function()
						require("syntax-tree-surfer").move("n", false)
						vim.cmd(vim.api.nvim_replace_termcodes("normal zz", true, true, true))
					end,
					desc = "Swap next tree-sitter object",
				},
				["<a-up>"] = {
					function()
						require("syntax-tree-surfer").move("n", true)
						vim.cmd(vim.api.nvim_replace_termcodes("normal zz", true, true, true))
					end,
					desc = "Swap previous tree-sitter object",
				},
				["<a-left>"] = {
					function()
						require("syntax-tree-surfer").move("n", true)
						vim.cmd(vim.api.nvim_replace_termcodes("normal zz", true, true, true))
					end,
					desc = "Swap previous tree-sitter object",
				},
				["<C-d>"] = { "<C-d>zz" },
				["<C-u>"] = { "<C-u>zz" },
				["n"] = { "nzzzv" },
				["N"] = { "Nzzzv" },
				["d"] = { [["_d]] },
			},
			v = {
				["s"] = {
					"<cmd>lua require('hop').hint_words({ extend_visual = true })<cr>",
				},
				["<S-s>"] = {
					"<cmd>lua require('hop').hint_lines({ extend_visual = true })<cr>",
				},
				["<leader>im"] = {
					function()
						require("telescope").extensions.goimpl.goimpl({})
					end,
					desc = "Go Interface Impl",
					silent = true,
					noremap = true,
				},
				["d"] = { [["_d]] },
			},
			[""] = {
				[":"] = { ";" },
				[";"] = { ":" },
			},
			x = {
				["J"] = { "<cmd>STSSelectNextSiblingNode<cr>", desc = "Surf next tree-sitter object" },
				["K"] = { "<cmd>STSSelectPrevSiblingNode<cr>", desc = "Surf previous tree-sitter object" },
				["H"] = { "<cmd>STSSelectParentNode<cr>", desc = "Surf parent tree-sitter object" },
				["L"] = { "<cmd>STSSelectChildNode<cr>", desc = "Surf child tree-sitter object" },
				["<c-j>"] = { "<cmd>STSSwapNextVisual<cr>", desc = "Surf next tree-sitter object" },
				["<c-l>"] = { "<cmd>STSSwapNextVisual<cr>", desc = "Surf next tree-sitter object" },
				["<c-k>"] = { "<cmd>STSSwapPrevVisual<cr>", desc = "Surf previous tree-sitter object" },
				["<c-h>"] = { "<cmd>STSSwapPrevVisual<cr>", desc = "Surf previous tree-sitter object" },
				["p"] = { [["_dP]] },
			},
			t = {
				["<C-\\>"] = { "<cmd>ToggleTerm<cr>", desc = "Toggle terminal" },
			},
		})
	)
end
