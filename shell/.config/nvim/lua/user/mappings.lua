local maps = { n = {} }
maps.n["<leader>db"] = maps.n["<leader>Db"]
maps.n["<leader>dB"] = maps.n["<leader>DB"]
maps.n["<leader>dc"] = maps.n["<leader>Dc"]

maps.n["<leader>di"] = maps.n["<leader>Di"]
maps.n["<leader>do"] = maps.n["<leader>Do"]
maps.n["<leader>dO"] = maps.n["<leader>DO"]
maps.n["<leader>dq"] = maps.n["<leader>Dq"]
maps.n["<leader>dQ"] = maps.n["<leader>DQ"]
maps.n["<leader>dp"] = maps.n["<leader>Dp"]
maps.n["<leader>dr"] = maps.n["<leader>Dr"]
maps.n["<leader>dR"] = maps.n["<leader>DR"]
maps.n["<leader>du"] = maps.n["<leader>Du"]
maps.n["<leader>dh"] = maps.n["<leader>Dh"]

return vim.tbl_deep_extend("force", maps, {
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
				end
			},
			["<C-x>"] = {
				function()
					require("dial.map").dec_normal()
				end
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
