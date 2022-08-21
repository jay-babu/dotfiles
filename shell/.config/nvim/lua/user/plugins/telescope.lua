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
			vimgrep_arguments = {
				"rg",
				"--color=never",
				"--no-heading",
				"-i",
				"--with-filename",
				"--line-number",
				"--column",
				"--hidden",
			},
			file_ignore_patterns = {
				".git",
				"node_modules",
			},
			preview = {
				mime_hook = function(filepath, bufnr, opts)
					local is_image = function(filepath)
						local image_extensions = { "png", "jpg", "gif" } -- Supported image formats
						local split_path = vim.split(filepath:lower(), ".", { plain = true })
						local extension = split_path[#split_path]
						return vim.tbl_contains(image_extensions, extension)
					end
					if is_image(filepath) then
						local term = vim.api.nvim_open_term(bufnr, {})
						local function send_output(_, data, _)
							for _, d in ipairs(data) do
								vim.api.nvim_chan_send(term, d .. "\r\n")
							end
						end
						vim.fn.jobstart({
							"catimg",
							filepath, -- Terminal image viewer command
						}, { on_stdout = send_output, stdout_buffered = true })
					else
						require("telescope.previewers.utils").set_preview_message(
							bufnr,
							opts.winid,
							"Binary cannot be previewed"
						)
					end
				end,
			},
		},
		pickers = {
			find_files = {
				hidden = true,
			},
		},
		extensions = {
			media_files = {
				filetypes = { "png", "jpg", "mp4", "webm", "pdf", "gif" },
				find_cmd = "rg",
			},
		},
	}

	return vim.tbl_deep_extend("force", default, overrides)
end
