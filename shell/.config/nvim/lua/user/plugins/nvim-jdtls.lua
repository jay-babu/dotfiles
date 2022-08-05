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

local bundles = {}

vim.list_extend(bundles, vim.split(vim.fn.glob(home .. "/.local/share/vscode-java-decompiler/server/*jar"), "\n"))

local config = {
	cmd = {
		"java",
		"-Declipse.application=org.eclipse.jdt.ls.core.id1",
		"-Dosgi.bundles.defaultStartLevel=4",
		"-Declipse.product=org.eclipse.jdt.ls.core.product",
		"-Dlog.protocol=true",
		"-Dlog.level=ALL",
		"-Xms1g",
		"-javaagent:" .. vim.fn.stdpath("data") .. "/mason/packages/jdtls/lombok.jar",
		"-jar",
		vim.fn.stdpath("data")
			.. "/mason/packages/jdtls/plugins/org.eclipse.equinox.launcher_1.6.400.v20210924-0641.jar",
		"-configuration",
		vim.fn.stdpath("data") .. "/mason/packages/jdtls/config_linux",
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

			contentProvider = {
				preferred = "fernflower",
			},
			sources = {

				organizeImports = {
					starThreshold = 9999,
					staticStartThreshold = 9999,
				},
			},
		},
	},
}

require("jdtls").start_or_attach(config)

for _, line in ipairs(ws_folders_lsp) do
	vim.lsp.buf.add_workspace_folder(line)
end
