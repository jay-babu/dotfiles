return function(config)
	local null_ls = require("null-ls")
	local b = null_ls.builtins
	config.debug = false
	config.sources = {
		-- Lua
		b.formatting.stylua.with({}),
		-- b.diagnostics.luacheck,

		-- Shell
		b.formatting.shfmt,
		b.diagnostics.shellcheck.with({ diagnostics_format = "#{m} [#(c)]" }),

		-- Docker
		b.diagnostics.hadolint,

		b.diagnostics.ansiblelint,

		-- Golang
		b.diagnostics.staticcheck,
		-- b.formatting.gofumpt,

		-- JS
		b.formatting.eslint_d,
		b.diagnostics.eslint_d,
		b.code_actions.eslint_d,

		-- Protobuf
		b.formatting.protolint,
		b.diagnostics.protolint,

		-- Rust
		b.formatting.rustfmt,

		b.code_actions.gitsigns,
	}
	config.on_attach = function(client)
		if client.resolved_capabilities.document_formatting then
			vim.api.nvim_create_autocmd("BufWritePre", {
				desc = "Auto format before save",
				pattern = "<buffer>",
				callback = vim.lsp.buf.formatting_sync,
			})
		end
	end
	return config
end
