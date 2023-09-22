return function(default)
	default.n["<S-h>"] = default.n["[b"]
	default.n["<S-l>"] = default.n["]b"]
	default.n["[b"] = nil
	default.n["]b"] = nil
	default.n["<leader>db"] = nil
	default.n["<leader>dB"] = nil
	default.n["<leader>dC"] = nil
	return astronvim.user_opts(
		"work.mappings",
		require("astronvim.utils").extend_tbl(default, {
			n = {
				["<C-\\>"] = { "<cmd>ToggleTerm<cr>", desc = "Toggle terminal" },
				["<C-Down>"] = false,
				["<C-Left>"] = false,
				["<C-Right>"] = false,
				["<C-Up>"] = false,
				["<C-s>"] = false,
				["<leader>db"] = false,
				["<leader>dB"] = false,
				["<leader>dC"] = false,

				-- disable <leader>b mappings
				["<leader>b"] = false,
				["<leader>bb"] = false,
				["<leader>bd"] = false,
				["<leader>b\\"] = false,
				["<leader>b|"] = false,

				["<leader>z"] = {
					desc = "True Zen",
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
				["<leader>c"] = function()
					if vim.o.filetype == "sql" then
						require("astronvim.utils.buffer").close(0, true)
					else
						require("astronvim.utils.buffer").close()
					end
				end,
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
				-- Treesitter Surfer
				["<a-down>"] = {
					function()
						require("syntax-tree-surfer").move("n", false)
						-- vim.cmd(vim.api.nvim_replace_termcodes("normal zz", true, true, true))
					end,
					desc = "Swap next tree-sitter object",
				},
				["<a-right>"] = {
					function()
						require("syntax-tree-surfer").move("n", false)
					end,
					desc = "Swap next tree-sitter object",
				},
				["<a-up>"] = {
					function()
						require("syntax-tree-surfer").move("n", true)
					end,
					desc = "Swap previous tree-sitter object",
				},
				["<a-left>"] = {
					function()
						require("syntax-tree-surfer").move("n", true)
					end,
					desc = "Swap previous tree-sitter object",
				},
				["<C-d>"] = { "<C-d>zz" },
				["<C-u>"] = { "<C-u>zz" },
				["n"] = { "nzzzv" },
				["N"] = { "Nzzzv" },
				["d"] = { [["_d]] },
				["<leader>tc"] = {
					function()
						require("neotest").run.run()
					end,
					desc = "Run nearest test",
				},
				["<leader>tm"] = {
					function()
						require("neotest").run.run(vim.fn.expand("%"))
					end,
					desc = "Run tests in file",
				},
				["<leader>to"] = {
					function()
						require("neotest").output.open({ enter = true })
					end,
					desc = "Toggle test output",
				},
			},
			v = {
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
