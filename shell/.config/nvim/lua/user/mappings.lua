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
}
