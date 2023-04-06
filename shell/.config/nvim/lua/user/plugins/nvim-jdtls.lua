return {
	{
		"mfussenegger/nvim-jdtls",
		ft = {
			"java",
		},
		dependencies = {
			"neovim/nvim-lspconfig",
		},
		opts = function(_, opts)
			local root_dir = require("jdtls.setup").find_root({ "packageInfo" }, "Config")
			local home = os.getenv("HOME")
			local extendedClientCapabilities = require("jdtls").extendedClientCapabilities
			extendedClientCapabilities.resolveAdditionalTextEditsSupport = true

			local ws_folders_jdtls = {}
			if root_dir then
				local file = io.open(root_dir .. "/.bemol/ws_root_folders", "r")
				if file then
					for line in file:lines() do
						table.insert(ws_folders_jdtls, string.format("file://%s", line))
					end
					file:close()
				end
			end

			local bundles = opts.bundles
				or {
					vim.fn.glob(
						require("mason-registry").get_package("java-debug-adapter"):get_install_path()
							.. "/extension/server/com.microsoft.java.debug.plugin-*.jar"
					),
					-- unpack remaining bundles
					(table.unpack or unpack)(
						vim.split(
							vim.fn.glob(
								require("mason-registry").get_package("java-test"):get_install_path()
									.. "/extension/server/*.jar"
							),
							"\n",
							{}
						)
					),
				}
			vim.list_extend(
				bundles,
				vim.split(vim.fn.glob(home .. "/.local/share/vscode-java-decompiler/server/*jar"), "\n")
			)

			opts.root_dir = root_dir
			opts.init_options.bundles = bundles
			opts.init_options.workspaceFolders = ws_folders_jdtls
			opts.settings = require("astronvim.utils").extend_tbl(opts.settings, {
				java = {
					signatureHelp = {
						enabled = true,
					},
					eclipse = {
						downloadSources = true,
					},
					configuration = {
						updateBuildConfiguration = "interactive",
					},
					maven = {
						downloadSources = true,
					},
					implementationsCodeLens = {
						enabled = true,
					},
					referencesCodeLens = {
						enabled = false,
					},
					references = {
						includeDecompiledSources = false,
					},
					inlayHints = {
						parameterNames = {
							enabled = "all", -- literals, all, none
						},
					},
					completion = {
						guessMethodArguments = true,
						favoriteStaticMembers = {
							"java.util.Objects.requireNonNull",
							"java.util.Objects.requireNonNullElse",
							"org.assertj.core.api.Assertions.*",
							"org.hamcrest.CoreMatchers.*",
							"org.hamcrest.Matchers.*",
							"org.junit.jupiter.api.Assertions.*",
							"org.mockito.Mockito.*",
						},
					},
					contentProvider = {
						preferred = "fernflower",
					},
					extendedClientCapabilities = extendedClientCapabilities,
					sources = {
						organizeImports = {
							starThreshold = 9999,
							staticStartThreshold = 9999,
						},
					},
					flags = {
						allow_incremental_sync = true,
					},
				},
			})
			return opts
		end,
	},
}
