return {
	"nvim-telescope/telescope.nvim",
	opts = function(_, opts)
		return require("astronvim.utils").extend_tbl(opts, {
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
				vimgrep_arguments = {
					"rg",
					"--color=never",
					"--no-heading",
					"-i",
					"--with-filename",
					"--line-number",
					"--column",
					"--hidden",
					"--follow",
				},
				file_ignore_patterns = {
					".git",
					"node_modules",
					".bemol",
				},
			},
			pickers = {
				find_files = {
					hidden = true,
					follow = true,
				},
			},
		})
	end,
}
