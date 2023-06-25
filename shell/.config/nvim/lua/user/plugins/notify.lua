return {
	"rcarriga/nvim-notify",
	init = function()
		require("astronvim.utils").load_plugin_with_func("nvim-notify", vim, "notify")
	end,
	opts = {
		background_colour = "#000000",
	},
}
