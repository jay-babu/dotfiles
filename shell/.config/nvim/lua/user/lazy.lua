return function(config)
	config = require("astronvim.utils").extend_tbl(config, {
		dev = {
			path = "~/code",
		},
	})
	return astronvim.user_opts("work.lazy", config)
end
