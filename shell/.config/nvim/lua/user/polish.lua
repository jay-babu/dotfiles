return function()
	-- code

	vim.api.nvim_create_autocmd({ "VimEnter", "ColorScheme" }, {
		desc = "Set up telescope theme",
		pattern = "*",
		callback = require("user.theme").telescope_theme,
	})
	-- Create an autocmd User PackerCompileDone to update it every time packer is compiled
	-- vim.api.nvim_create_autocmd("User", {
	-- 	pattern = "PackerCompileDone",
	-- 	callback = function()
	-- 		vim.cmd("CatppuccinCompile")
	-- 		vim.defer_fn(function()
	-- 			vim.cmd("colorscheme catppuccin")
	-- 		end, 0) -- Defered for live reloading
	-- 	end,
	-- })
end
