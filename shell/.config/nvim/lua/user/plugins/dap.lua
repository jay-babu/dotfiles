return {
	"mfussenegger/nvim-dap",
	dependencies = {
		{ "theHamsta/nvim-dap-virtual-text", config = true },
		{ "jbyuki/one-small-step-for-vimkind" },
	},
	config = function(_, _)
		vim.fn.sign_define("DapStopped", { text = "", texthl = "DiagnosticWarn" })
		vim.fn.sign_define("DapBreakpoint", { text = "", texthl = "DiagnosticInfo" })
		vim.fn.sign_define("DapBreakpointRejected", { text = "", texthl = "DiagnosticError" })
		vim.fn.sign_define("DapBreakpointCondition", { text = "", texthl = "DiagnosticInfo" })
		vim.fn.sign_define("DapLogPoint", { text = ".>", texthl = "DiagnosticInfo" })

		-- Catppuccin
		local sign = vim.fn.sign_define

		sign("DapBreakpoint", { text = "●", texthl = "DapBreakpoint", linehl = "", numhl = "" })
		sign("DapBreakpointCondition", { text = "●", texthl = "DapBreakpointCondition", linehl = "", numhl = "" })
		sign("DapLogPoint", { text = "◆", texthl = "DapLogPoint", linehl = "", numhl = "" })

		local dap = require("dap")
		dap.configurations.lua = {

			{

				type = "nlua",
				request = "attach",
				name = "Attach to running Neovim instance",
			},
		}

		dap.adapters.nlua = function(callback, config)
			callback({ type = "server", host = config.host or "127.0.0.1", port = config.port or 8086 })
		end
	end,
}
