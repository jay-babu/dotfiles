return {
	"nvim-neo-tree/neo-tree.nvim",
	opts = {
		close_if_last_window = true,
		enable_diagnostics = true,
		filesystem = {
			filtered_items = {
				hide_dotfiles = false,
				hide_gitignored = false,
			},
			group_empty_dirs = true,
			follow_current_file = {
				enabled = true,
			},
		},
		sort_case_insensitive = true,
		renderers = {
			directory = {
				{ "indent" },
				{ "icon" },
				{ "current_filter" },
				{ "name" },
				{ "clipboard" },
				{ "diagnostics", errors_only = true },
			},
			file = {
				{ "indent" },
				{ "icon" },
				{
					"name",
					use_git_status_colors = true,
					zindex = 10,
				},
				{ "clipboard" },
				{ "bufnr" },
				{ "modified" },
				{ "diagnostics" },
				{ "git_status" },
			},
		},
		window = {
			position = "float",
			width = "100%",
		},
	},
}
