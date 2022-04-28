return function(plugins)
  local user_plugins = {
    {
      "catppuccin/nvim",
      as = "catppuccin",
      config = function ()
        -- code
        require("catppuccin").setup {}
      end
    },
  }

  return vim.tbl_deep_extend("force", plugins, user_plugins)
end

