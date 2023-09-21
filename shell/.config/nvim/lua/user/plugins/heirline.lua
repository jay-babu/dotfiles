return {
	{
		"rebelot/heirline.nvim",
		opts = function(_, opts)
			opts.tabline = nil -- remove tabline

			return opts
		end,
	},
}
