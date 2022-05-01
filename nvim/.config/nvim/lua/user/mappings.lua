return {
	setup = function()
		local unmap = vim.keymap.del
		local map = vim.keymap.set

		-- use semicolon instead of colon
		map("", ";", ":")
		map("", ":", ";")
	end,
}
