return astronvim.user_opts("work.lsp.formatting", {
	format_on_save = {
		enabled = true,
	},
	filter = function(client)
		if vim.bo.filetype == "java" then
			return client.name == "null-ls"
		end
		return true
	end,
})
