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
				name = "WslClipboard",
				copy = {
					["+"] = "clip.exe",
					["*"] = "clip.exe",
				},
				paste = {
					["+"] = 'powershell.exe -c [Console]::Out.Write($(Get-Clipboard -Raw).tostring():gsub("\r", ""))',
					["*"] = 'powershell.exe -c [Console]::Out.Write($(Get-Clipboard -Raw).tostring():gsub("\r", ""))',
				},
				cache_enabled = 0,
			},
		},
	})
end
return astronvim.user_opts("work.options", M)
