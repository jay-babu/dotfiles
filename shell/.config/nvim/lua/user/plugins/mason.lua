return {
	{
		"WhoIsSethDaniel/mason-tool-installer.nvim",
		build = ":MasonToolsUpdate",
		opts = {
			ensure_installed = {
				"gofumpt",
				"golines",
				"gotests",
				"chrome-debug-adapter",
				"impl",
				"json-to-struct",
				"luacheck",
				"pyright",
				"rust-analyzer",
				"solidity",
			},
			auto_update = true,
			run_on_start = false,
		},
	},
	{
		"williamboman/mason-lspconfig.nvim",
		opts = {
			ensure_installed = {
				"ansiblels",
				"cssls",
				"dockerls",
				"gopls",
				"graphql",
				"html",
				"jdtls",
				"jsonls",
				"kotlin_language_server",
				"pyright",
				"rust_analyzer",
				"solc",
				"lua_ls",
				"tsserver",
			},
		},
	},
	{
		"jay-babu/mason-null-ls.nvim",
		opts = {
			ensure_installed = {
				"black",
				"google_java_format",
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
			},
			handlers = {
				shellcheck = function()
					local null_ls = require("null-ls")
					null_ls.register(
						null_ls.builtins.diagnostics.shellcheck.with({ diagnostics_format = "#{m} [#(c)]" })
					)
				end,
			},
		},
	},
	{
		"jay-babu/mason-nvim-dap.nvim",
		opts = {
			ensure_installed = {
				"delve",
				"js",
				"python",
				"javadbg",
				"javatest",
			},
		},
	},
}
