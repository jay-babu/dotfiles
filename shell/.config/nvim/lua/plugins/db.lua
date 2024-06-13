return {
  {
    "kristijanhusak/vim-dadbod-ui",
    dependencies = {
      { "tpope/vim-dadbod", lazy = true },
      { "kristijanhusak/vim-dadbod-completion", ft = { "sql", "mysql", "plsql" }, lazy = true },
    },
    cmd = {
      "DBUI",
      "DBUIToggle",
      "DBUIAddConnection",
      "DBUIFindBuffer",
    },

    init = function()
      -- Your DBUI configuration
      vim.g.db_ui_use_nerd_fonts = 1
      vim.g.completion_matching_ignore_case = 1
    end,
  },
  {
    "AstroNvim/astrocore",
    autocmds = {
      dadbod = {
        event = "FileType",
        desc = "Dadbod Enable on filetypes",
        pattern = "sql,mysql,plsql,pg",
        callback = function()
          require("cmp").setup.buffer {
            sources = {
              { name = "vim-dadbod-completion" },
            },
          }
        end,
      },
      pg_file = {
        event = { "BufRead", "BufNewFile" },
        pattern = "*.pg",
        command = "set filetype=sql",
      },
    },
  },
}
