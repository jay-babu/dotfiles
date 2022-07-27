local status_ok, mason_lspconfig = pcall(require, "mason-lspconfig")
if not status_ok then
	print("mason-lspconfig did not load")
	return
end
mason_lspconfig.setup({
	automatic_installation = true,
})
