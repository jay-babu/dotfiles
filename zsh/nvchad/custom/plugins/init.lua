local customPlugins = require "core.customPlugins"

customPlugins.add(function(use)
  use "nathom/filetype.nvim"

  use {
    "TovarishFin/vim-solidity",
    ft = { 'solidity' },
  }

  use {
    "windwp/nvim-ts-autotag",
    ft = { 'html', 'javascript', 'javascriptreact', 'typescriptreact', 'svelte', 'vue' },
    after = "nvim-treesitter",
    config = function()
      require("nvim-ts-autotag").setup()
    end,
  }

   use {
    "Pocco81/TrueZen.nvim",
    cmd = {
       "TZAtaraxis",
       "TZMinimalist",
       "TZFocus",
    },
    config = function()
       require "custom.plugins.truezen"
    end,
   }
end)
