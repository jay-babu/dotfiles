local root_dir = require("jdtls.setup").find_root({ "packageInfo" }, "Config")
local home = os.getenv("HOME")
local eclipse_workspace = home .. "/.local/share/eclipse/" .. vim.fn.fnamemodify(root_dir, ":p:h:t")

local ws_folders_lsp = {}
local ws_folders_jdtls = {}
if root_dir then
	local file = io.open(root_dir .. "/.bemol/ws_root_folders", "r")
	if file then
		for line in file:lines() do
			table.insert(ws_folders_lsp, line)
			table.insert(ws_folders_jdtls, string.format("file://%s", line))
		end
		file:close()
	end
end

local extendedClientCapabilities = require("jdtls").extendedClientCapabilities
extendedClientCapabilities.resolveAdditionalTextEditsSupport = true

local bundles = {}

-- get the mason install path
local install_path = require("mason-registry").get_package("jdtls"):get_install_path()

vim.list_extend(bundles, vim.split(vim.fn.glob(home .. "/.local/share/vscode-java-decompiler/server/*jar"), "\n"))

-- get the current OS
local operating_system
if vim.fn.has("macunix") then
	operating_system = "mac"
elseif vim.fn.has("win32") then
	operating_system = "win"
else
	operating_system = "linux"
end

local config = {
	cmd = {
		"java",
		"-Declipse.application=org.eclipse.jdt.ls.core.id1",
		"-Dosgi.bundles.defaultStartLevel=4",
		"-Declipse.product=org.eclipse.jdt.ls.core.product",
		"-Dlog.protocol=true",
		"-Dlog.level=ALL",
		"-Xms1g",
		"-javaagent:" .. install_path .. "/lombok.jar",
		"-jar",
		vim.fn.glob(install_path .. "/plugins/org.eclipse.equinox.launcher_*.jar"),
		"-configuration",
		vim.fn.stdpath("data") .. "/mason/packages/jdtls/config_" .. operating_system,
		"-data",
		eclipse_workspace,
		"--add-modules=ALL-SYSTEM",
		"--add-opens",
		"java.base/java.util=ALL-UNNAMED",
		"--add-opens",
		"java.base/java.lang=ALL-UNNAMED",
	},
	root_dir = root_dir,
	init_options = {
		workspaceFolders = ws_folders_jdtls,
		bundles = bundles,
	},
	settings = {
		java = {
			signatureHelp = {
				enabled = true,
			},
			eclipse = {
				downloadSources = true,
			},
			configuration = {

				updateBuildConfiguration = "interactive",
				-- runtimes = {
				--   {
				--     name = "JavaSE-17",
				--     path = "/home/jrakhman/.sdkman/candidates/java/17.0.4-oracle",
				--   },
				-- },
			},
			maven = {
				downloadSources = true,
			},
			implementationsCodeLens = {
				enabled = true,
			},

			referencesCodeLens = {
				enabled = true,
			},
			references = {
				includeDecompiledSources = true,
			},
			inlayHints = {
				parameterNames = {
					enabled = "all", -- literals, all, none
				},
			},
			completion = {
				favoriteStaticMembers = {
					"org.hamcrest.MatcherAssert.assertThat",
					"org.hamcrest.Matchers.*",
					"org.hamcrest.CoreMatchers.*",
					"org.junit.jupiter.api.Assertions.*",
					"java.util.Objects.requireNonNull",
					"java.util.Objects.requireNonNullElse",
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
	},
}

require("jdtls").start_or_attach(config)

for _, line in ipairs(ws_folders_lsp) do
	vim.lsp.buf.add_workspace_folder(line)
end
