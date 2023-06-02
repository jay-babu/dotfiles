local M = {
	opt = {
		wildmode = "longest:full,full",
		shell = vim.fn.exepath("bash"),
	},
	o = {
		signcolumn = "yes",
	},
	g = {
		resession_enabled = true,
	},
}

if vim.fn.has("wsl") == 1 then
	M = require("astronvim.utils").extend_tbl(M, {
		g = {
			clipboard = {
				name = "win32yank-wsl",
				copy = {
					["+"] = "win32yank.exe -i --crlf",
					["*"] = "win32yank.exe -i --crlf",
				},
				paste = {
					["+"] = "win32yank.exe -o --lf",
					["*"] = "win32yank.exe -o --lf",
				},
				cache_enabled = 0,
			},
		},
	})
end
return astronvim.user_opts("work.options", M)
