return astronvim.user_opts("work.options", {
	opt = {
		wildmode = "longest:full,full",
		shell = vim.fn.exepath("bash"),
	},
	o = {
		signcolumn = "yes",
	},
	g = {
		lsp_handlers_enabled = false,
	},
})
