return function()
	local ok, p = pcall(require, "user.work.polish")
	if ok then
		require("astronvim.utils").conditional_func(p, true)
	end
end
