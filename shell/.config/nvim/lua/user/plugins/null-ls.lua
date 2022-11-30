return function(config)
	local sources = {
		"black",
		"eslint_d",
		"flake8",
		"hadolint",
		"isort",
		"protolint",
		"shfmt",
		"staticcheck",
		"stylua",
		"hadolint",
		"ansiblelint",
		"rustfmt",
		"gitsigns",
		"trim_whitespace",
		"todo_comments",
	}

	local null_ls_sources = {}

	for _, source in ipairs(sources) do
		for _, method in ipairs({ "diagnostics", "formatting", "code_actions", "completion", "hover" }) do
			local ok, null_ls_source = pcall(require, string.format("null-ls.builtins.%s.%s", method, source))
			if ok then
				table.insert(null_ls_sources, null_ls_source)
			end
		end
	end

	local null_ls = require("null-ls")
	local b = null_ls.builtins
	vim.list_extend(null_ls_sources, {
		b.diagnostics.shellcheck.with({ diagnostics_format = "#{m} [#(c)]" }),
	})

	config.debug = false
	config.sources = null_ls_sources
	return config
end
