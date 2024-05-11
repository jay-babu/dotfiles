require("lazy").setup({
  {
    "AstroNvim/AstroNvim",
    version = "^4",
    import = "astronvim.plugins",
    opts = { -- AstroNvim options must be set here with the `import` key
      mapleader = " ", -- This ensures the leader key must be configured before Lazy is set up
      maplocalleader = ",", -- This ensures the localleader key must be configured before Lazy is set up
      icons_enabled = true, -- Set to false to disable icons (if no Nerd Font is available)
    },
  },
  {
    "stevearc/profile.nvim",
    lazy = false,
    priority = 10000,
    name = "profile",
    config = function()
      local should_profile = os.getenv "NVIM_PROFILE"
      if should_profile then
        require("profile").instrument_autocmds()
        if should_profile:lower():match "^start" then
          require("profile").start "*"
        else
          require("profile").instrument "*"
        end
      end

      vim.keymap.set("", "<f1>", function()
        local prof = require "profile"
        if prof.is_recording() then
          prof.stop()
          prof.export "profile.json"
          vim.notify(string.format("Wrote %s", "profile.json"))
        else
          prof.start "*"
        end
      end)
    end,
  },
  { import = "community" },
  { import = "plugins" },
} --[[@as LazySpec]], {
  -- Configure any other `lazy.nvim` configuration options here
  install = { colorscheme = { "astrodark", "habamax" } },
  performance = {
    rtp = {
      -- disable some rtp plugins, add more to your liking
      disabled_plugins = {
        "gzip",
        "netrwPlugin",
        "tarPlugin",
        "tohtml",
        "zipPlugin",
      },
    },
  },
} --[[@as LazyConfig]])
