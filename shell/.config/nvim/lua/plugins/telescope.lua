return {
  "nvim-telescope/telescope.nvim",
  opts = function(_, opts)
    return require("astrocore").extend_tbl(opts, {
      defaults = {
        vimgrep_arguments = {
          "rg",
          "--color=never",
          "--no-heading",
          "-i",
          "--with-filename",
          "--line-number",
          "--column",
          "--hidden",
          "--follow",
        },
        file_ignore_patterns = {
          ".git",
          "node_modules",
          ".bemol",
        },
      },
      pickers = {
        find_files = {
          hidden = true,
          follow = true,
        },
      },
    })
  end,
}
