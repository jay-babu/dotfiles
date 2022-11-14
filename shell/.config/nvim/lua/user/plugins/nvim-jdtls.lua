local root_dir = require("jdtls.setup").find_root({ "packageInfo" }, "Config")

local ws_folders_lsp = {}
if root_dir then
	local file = io.open(root_dir .. "/.bemol/ws_root_folders", "r")
	if file then
		for line in file:lines() do
			table.insert(ws_folders_lsp, line)
		end
		file:close()
	end
end

for _, line in ipairs(ws_folders_lsp) do
	vim.lsp.buf.add_workspace_folder(line)
end
