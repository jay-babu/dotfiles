return {
  {
    "ibhagwan/fzf-lua",
    optional = true,
    opts = {
      grep = {
        rg_opts = [[--column --line-number --no-heading --color=always --smart-case --hidden --glob='!.git/**' --glob='!.jj/**' --max-columns=4096 -e]],
      },
    },
  },
}
