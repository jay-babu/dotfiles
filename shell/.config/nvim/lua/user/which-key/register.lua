return {
	n = {
		["<leader>"] = {
			x = {
				name = "Debugger",
				b = {
					function()
						require("dap").toggle_breakpoint()
					end,
					"Toggle Breakpoint",
				},
				B = {
					function()
						require("dap").clear_breakpoints()
					end,
					"Clear Breakpoints",
				},
				c = {
					function()
						require("dap").continue()
					end,
					"Continue",
				},
				i = {
					function()
						require("dap").step_into()
					end,
					"Step Into",
				},
				l = {
					function()
						require("dapui").float_element("breakpoints")
					end,
					"List Breakpoints",
				},
				o = {
					function()
						require("dap").step_over()
					end,
					"Step Over",
				},
				q = {
					function()
						require("dap").close()
					end,
					"Close Session",
				},
				Q = {
					function()
						require("dap").terminate()
					end,
					"Terminate",
				},
				r = {
					function()
						require("dap").repl.toggle()
					end,
					"REPL",
				},
				s = {
					function()
						require("dapui").float_element("scopes")
					end,
					"Scopes",
				},
				t = {
					function()
						require("dapui").float_element("stacks")
					end,
					"Threads",
				},
				u = {
					function()
						require("dapui").toggle()
					end,
					"Toggle Debugger UI",
				},
				w = {
					function()
						require("dapui").float_element("watches")
					end,
					"Watches",
				},
				x = {
					function()
						require("dap.ui.widgets").hover()
					end,
					"Inspect",
				},
			},
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
	v = {
		["<leader>"] = {
			x = {
				name = "Debugger",
				e = {
					function()
						require("dapui").eval()
					end,
					"Evaluate Line",
				},
			},
		},
	},
}
