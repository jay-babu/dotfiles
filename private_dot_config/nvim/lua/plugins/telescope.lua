return {
  {
    "nvim-telescope/telescope.nvim",
    optional = true,
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
  },
  {
    "ibhagwan/fzf-lua",
    optional = true,
    opts = {
      grep = {
        rg_opts = [[--column --line-number --no-heading --color=always --smart-case --hidden --follow --max-columns=4096 -e]],
      },
    },
  },
}
