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

		-- All
		b.formatting.trim_whitespace,
		b.diagnostics.todo_comments,
	}
	return config
end
