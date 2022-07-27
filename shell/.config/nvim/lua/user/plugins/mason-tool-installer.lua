local status_ok, mason_tool_installer = pcall(require, "mason-tool-installer")
if not status_ok then
	print("mason-tool-installer did not load")
	return
end
mason_tool_installer.setup({
	ensure_installed = {
		"debugpy",
		"delve",
		"eslint_d",
		"gofumpt",
		"golines",
		"gotests",
		"impl",
		"json-to-struct",
		"luacheck",
		"shellcheck",
		"shfmt",
		"staticcheck",
	},
	auto_update = true,
	run_on_start = false,
})
