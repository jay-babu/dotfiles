local null_ls = require('null-ls')
local b = null_ls.builtins

local sources = {
	-- webdev
	b.formatting.eslint,

	-- Lua
	b.formatting.stylua.with({}),
	b.diagnostics.luacheck,

	-- Shell
	b.formatting.shfmt,
	b.diagnostics.shellcheck.with({ diagnostics_format = '#{m} [#(c)]' }),
}

local M = {}

M.setup = function()
	null_ls.setup({
		debug = true,
		sources = sources,

		-- format on save
		on_attach = function(client)
			if client.resolved_capabilities.document_formatting then
				vim.cmd('autocmd BufWritePre <buffer> lua vim.lsp.buf.formatting_sync()')
			end
		end,
	})
end

return M
