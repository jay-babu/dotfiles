return function(config)
	config = vim.tbl_deep_extend("force", config, {
		dev = {
			path = "~/code",
		},
	})
	return astronvim.user_opts("work.lazy", config)
end
