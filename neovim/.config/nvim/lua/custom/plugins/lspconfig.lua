local M = {}

M.setup_lsp = function(attach, capabilities)
	local lspconfig = require('lspconfig')

	lspconfig.tsserver.setup({
		on_attach = function(client, bufnr)
			client.resolved_capabilities.document_formatting = false
			vim.api.nvim_buf_set_keymap(bufnr, 'n', '<space>fm', '<cmd>lua vim.lsp.buf.formatting()<CR>', {})
			attach(client)
		end,
	})

	-- lspservers with default config
	local servers = {
		'bashls',
		'clangd',
		'cssls',
		'gopls',
		'graphql',
		'html',
		'pyright',
		'solidity_ls',
	}

	for _, lsp in ipairs(servers) do
		lspconfig[lsp].setup({
			on_attach = function(client)
				attach(client)
			end,
			capabilities = capabilities,
			flags = {
				debounce_text_changes = 150,
			},
		})
	end

	-- lua lsp!
	-- local sumneko_root_path = '/home/jay/dotfiles/neovim/.config/nvim/lua/custom/lua-language-server'
	-- local sumneko_binary = sumneko_root_path .. '/bin/lua-language-server'
	--
	-- lspconfig.sumneko_lua.setup({
	-- 	cmd = { sumneko_binary, '-E', sumneko_root_path .. '/main.lua' },
	-- 	on_attach = function(client)
	-- 		attach(client)
	-- 	end,
	-- 	capabilities = capabilities,
	-- 	flags = {
	-- 		debounce_text_changes = 150,
	-- 	},
	-- 	settings = {
	-- 		Lua = {
	-- 			diagnostics = {
	-- 				globals = { 'vim' },
	-- 			},
	-- 			workspace = {
	-- 				library = {
	-- 					[vim.fn.expand('$VIMRUNTIME/lua')] = true,
	-- 					[vim.fn.expand('$VIMRUNTIME/lua/vim/lsp')] = true,
	-- 				},
	-- 				maxPreload = 100000,
	-- 				preloadFileSize = 10000,
	-- 			},
	-- 		},
	-- 	},
	-- })
end

return M
