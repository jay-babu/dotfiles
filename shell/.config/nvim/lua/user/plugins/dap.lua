local dap = require("dap")
dap.adapters.python = {
	type = "executable",
	command = "/usr/bin/python3",
	args = {
		"-m",
		"debugpy.adapter",
	},
}

dap.configurations.python = {
	{
		type = "python",
		request = "launch",
		name = "Launch file",
		program = "${file}", -- This configuration will launch the current file if used.
	},
}
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
