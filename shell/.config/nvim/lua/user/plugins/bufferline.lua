return {
	options = {
		diagnostics = "nvim_lsp",
		close_command = function(bufnum)
			require("bufdelete").bufdelete(bufnum, true)
		end,
		color_icons = true,
		groups = {
			options = {
				-- when you re-enter a hidden group this options re-opens that group so the buffer is visible
				toggle_hidden_on_enter = true,
			},
			items = {
				{
					name = "Tests", -- Mandatory
					highlight = { underline = true, sp = "blue" }, -- Optional
					priority = 2, -- determines where it will appear relative to other groups (Optional)
					icon = "", -- Optional
					matcher = function(buf) -- Mandatory
						return buf.filename:match("%_test")
							or buf.filename:match("%_spec")
							or buf.filename:match("%Test")
					end,
				},
				{
					name = "Docs",
					highlight = { undercurl = true },
					icon = "",
					auto_close = true, -- whether or not close this group if it doesn't contain the current buffer
					matcher = function(buf)
						return buf.filename:match("%.md") or buf.filename:match("%.txt")
					end,
					separator = { -- Optional
						style = require("bufferline.groups").separator.tab,
					},
				},
			},
		},
	},
}
