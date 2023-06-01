return function()
	local p, ok = pcall(require, "user.work.polish")
	if ok then
		require("astronvim.utils").conditional_func(p)
	end
end
