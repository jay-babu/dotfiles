-- vim.api.nvim_create_autocmd("User", {
--   pattern = "LazySyncPre",
--   callback = function() require("astronvim.utils.updater").update() end,
-- })
-- vim.api.nvim_create_autocmd("User", {
--   pattern = "LazySync",
--   callback = function() require("astronvim.utils.mason").update() end,
-- })
vim.api.nvim_create_autocmd({ "BufRead", "BufNewFile" }, { pattern = "*.pg", command = "set filetype=sql" })
vim.api.nvim_create_autocmd("FileType", {
  pattern = "sql,mysql,plsql,pg",
  callback = function()
    require("cmp").setup.buffer {
      sources = {
        { name = "vim-dadbod-completion" },
      },
    }
  end,
})
