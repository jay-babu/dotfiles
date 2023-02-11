return astronvim.user_opts("work.options", {
	opt = {
		wildmode = "longest:full,full",
	},
	o = {
		signcolumn = "yes",
	},
	g = {
		lsp_handlers_enabled = false,
	},
})
