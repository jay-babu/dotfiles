return function()
	vim.api.nvim_create_autocmd("User", {
		pattern = "LazySyncPre",
		callback = function()
			require("astronvim.utils.updater").update()
		end,
	})
	vim.api.nvim_create_autocmd("User", {
		pattern = "LazySync",
		callback = function()
			require("astronvim.utils.mason").update()
		end,
	})
	local ok, p = pcall(require, "user.work.polish")
	if ok then
		require("astronvim.utils").conditional_func(p, true)
	end
end
