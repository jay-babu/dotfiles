local M = {
	opt = {
		wildmode = "longest:full,full",
		shell = vim.fn.exepath("bash"),
	},
	o = {
		signcolumn = "yes",
	},
	g = {
		resession_enabled = true,
	},
}

return astronvim.user_opts("work.options", M)
