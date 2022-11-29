return function()
	-- code

	vim.api.nvim_create_autocmd({ "VimEnter", "ColorScheme" }, {
		desc = "Set up telescope theme",
		pattern = "*",
		callback = require("user.theme").telescope_theme,
	})

	local numbertogglegroup = vim.api.nvim_create_augroup("numbertoggle", { clear = true })
	vim.api.nvim_create_autocmd({ "BufEnter", "FocusGained", "InsertLeave" }, {
		pattern = "*",
		callback = function()
			vim.wo.relativenumber = true
		end,
		group = numbertogglegroup,
	})
	vim.api.nvim_create_autocmd({ "BufLeave", "FocusLost", "InsertEnter" }, {
		pattern = "*",
		callback = function()
			vim.wo.relativenumber = false
		end,
		group = numbertogglegroup,
	})

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
				require("jdtls").start_or_attach(config)
			end
		end,
	})

	vim.api.nvim_create_autocmd({ "BufRead", "BufNewFile" }, {
		pattern = "*.smithy",
		callback = function()
			vim.cmd([[set filetype=smithy]])
		end,
	})
end
