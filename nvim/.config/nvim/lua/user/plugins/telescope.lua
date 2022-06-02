return function(default)
	local overrides = {
		defaults = {
			prompt_prefix = "  ",
			borderchars = {
				prompt = { "─", "│", "─", "│", "╭", "╮", "╯", "╰" },
				results = { "─", "▐", "─", "│", "╭", "▐", "▐", "╰" },
				preview = { " ", "│", " ", "▌", "▌", "╮", "╯", "▌" },
			},
			selection_caret = "  ",
			layout_config = {
				width = 0.90,
				height = 0.85,
				preview_cutoff = 120,
				horizontal = {
					preview_width = function(_, cols, _)
						return math.floor(cols * 0.6)
					end,
				},
				vertical = {
					width = 0.9,
					height = 0.95,
					preview_height = 0.5,
				},
				flex = {
					horizontal = {
						preview_width = 0.9,
					},
				},
			},
			layout_strategy = "horizontal",
		},
		pickers = {
			find_files = {
				hidden = true,
			},
		},
	}

	return vim.tbl_deep_extend("force", default, overrides)
end
