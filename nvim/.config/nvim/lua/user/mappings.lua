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
		map("n", "s", function()
			require("hop").hint_words()
		end)
		map("n", "<C-e>", "<cmd>Telescope harpoon marks<cr>", { desc = "View Harpoon Marks" })
		map("n", "<S-s>", "<cmd>lua require('hop').hint_lines()<cr>")
		map("v", "s", "<cmd>lua require('hop').hint_words({ extend_visual = true })<cr>")
		map("v", "<S-s>", "<cmd>lua require('hop').hint_lines({ extend_visual = true })<cr>")
	end,
}
