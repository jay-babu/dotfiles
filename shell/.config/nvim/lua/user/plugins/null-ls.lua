return function(config)
	local null_ls = require("null-ls")
	local b = null_ls.builtins
	config.debug = false
	config.sources = {
		b.diagnostics.shellcheck.with({ diagnostics_format = "#{m} [#(c)]" }),

		-- Docker
		b.diagnostics.hadolint,

		b.diagnostics.ansiblelint,

		-- Rust
		b.formatting.rustfmt,

		b.code_actions.gitsigns,

		-- All
		b.formatting.trim_whitespace,
		b.diagnostics.todo_comments,
	}
	return config
end
