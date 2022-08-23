return {
	n = {
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
		["<C-e>"] = {
			"<cmd>Telescope harpoon marks<cr>",
			desc = "View Harpoon Marks",
		},
		["<S-s>"] = {
			"<cmd>lua require('hop').hint_lines()<cr>",
		},
		-- Treesitter Surfer
		["<c-down>"] = { "<cmd>STSSwapDownNormal<cr>", desc = "Swap next tree-sitter object" },
		["<c-right>"] = { "<cmd>STSSwapDownNormal<cr>", desc = "Swap next tree-sitter object" },
		["<c-up>"] = { "<cmd>STSSwapUpNormal<cr>", desc = "Swap previous tree-sitter object" },
		["<c-left>"] = { "<cmd>STSSwapUpNormal<cr>", desc = "Swap previous tree-sitter object" },
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
	},
}
