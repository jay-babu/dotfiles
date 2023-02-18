return {
	"goolord/alpha-nvim",
	cmd = "Alpha",
	opts = function(_, dashboard)
		local handle = io.popen("figlet -c 'Flying Raijin\nLevel 2'")
		local result = ""
		if handle ~= nil then
			result = handle:read("*a")
			handle:close()
		end

		dashboard.section.header.val = vim.fn.split(result, "\n")

		vim.api.nvim_create_autocmd("UIEnter", {
			-- pattern = "UIEnter",
			callback = function()
				local stats = require("lazy").stats()
				local ms = (math.floor(stats.startuptime * 100 + 0.5) / 100)
				dashboard.section.footer.val = {
					" ",
					" ",
					" ",
					"AstroNvim loaded " .. require("lazy").stats().count .. " plugins  in " .. ms .. " ms",
				}
			end,
		})

		return dashboard
	end,
}
