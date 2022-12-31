-- Options for language specific keymap
local opts = {
	mode = "n", -- NORMAL mode
	prefix = "<leader>",
	buffer = nil, -- Global mappings. Specify a buffer number for buffer local mappings
	silent = true, -- use `silent` when creating keymaps
	noremap = true, -- use `noremap` when creating keymaps
	nowait = true, -- use `nowait` when creating keymaps
}

local vopts = {
	mode = "v", -- VISUAL mode
	prefix = "<leader>",
	buffer = nil, -- Global mappings. Specify a buffer number for buffer local mappings
	silent = true, -- use `silent` when creating keymaps
	noremap = true, -- use `noremap` when creating keymaps
	nowait = true, -- use `nowait` when creating keymaps
}

return astronvim.user_plugin_opts("polish", function()
	-- code

	-- vim.api.nvim_create_autocmd({ "VimEnter", "ColorScheme" }, {
	-- 	desc = "Set up telescope theme",
	-- 	pattern = "*",
	-- 	callback = require("user.theme").telescope_theme,
	-- })

	if vim.fn.has("wsl") == 1 then
		vim.api.nvim_exec(
			[[
			let g:clipboard = {
          \   'name': 'win32yank-wsl',
          \   'copy': {
          \      '+': 'win32yank.exe -i --crlf',
          \      '*': 'win32yank.exe -i --crlf',
          \    },
          \   'paste': {
          \      '+': 'win32yank.exe -o --lf',
          \      '*': 'win32yank.exe -o --lf',
          \   },
          \   'cache_enabled': 0,
          \ }
		]],
			true
		)
	end

	vim.api.nvim_create_autocmd("Filetype", {
		pattern = "java", -- autocmd to start jdtls
		callback = function()
			local config = astronvim.lsp.server_settings("jdtls")
			if config.root_dir and config.root_dir ~= "" then
				config["on_attach"] = function(client, bufnr)
					vim.lsp.codelens.refresh()
					require("jdtls.dap").setup_dap_main_class_configs()
					require("jdtls").setup_dap({ hotcodereplace = "auto" })
					astronvim.lsp.on_attach(client, bufnr)
				end

				require("jdtls").start_or_attach(config)
				local mappings = {
					c = {
						o = { "<Cmd>lua require'jdtls'.organize_imports()<CR>", "Organize Imports" },
						v = { "<Cmd>lua require('jdtls').extract_variable()<CR>", "Extract Variable" },
						c = { "<Cmd>lua require('jdtls').extract_constant()<CR>", "Extract Constant" },
						t = { "<Cmd>lua require'jdtls'.test_nearest_method()<CR>", "Test Method" },
						T = { "<Cmd>lua require'jdtls'.test_class()<CR>", "Test Class" },
					},
				}

				local vmappings = {
					c = {
						v = { "<Esc><Cmd>lua require('jdtls').extract_variable(true)<CR>", "Extract Variable" },
						c = { "<Esc><Cmd>lua require('jdtls').extract_constant(true)<CR>", "Extract Constant" },
						m = { "<Esc><Cmd>lua require('jdtls').extract_method(true)<CR>", "Extract Method" },
					},
				}
				local status_ok, which_key = pcall(require, "which-key")
				if not status_ok then
					return
				end

				which_key.register(mappings, opts)
				which_key.register(vmappings, vopts)
			end
		end,
	})

	vim.api.nvim_create_autocmd({ "BufRead", "BufNewFile" }, {
		pattern = "*.smithy",
		callback = function()
			vim.cmd([[set filetype=smithy]])
		end,
	})
end, nil, "work")
