return {
	setup = function()
		local unmap = vim.keymap.del
		local map = vim.keymap.set

		-- use semicolon instead of colon
		map("", ";", ":")
		map("", ":", ";")

		-- harpoon
		map("n", "<leader>a", function()
			require("harpoon.mark").add_file()
		end, { desc = "Add File Harpoon" })
		map("n", "<C-e>", "<cmd>Telescope harpoon marks<cr>", { desc = "View Harpoon Marks" })
	end,
}
