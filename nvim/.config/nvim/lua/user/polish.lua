return function ()
  -- code
  
  vim.api.nvim_create_autocmd({ "VimEnter", "ColorScheme" }, {
    desc = "Set up telescope theme",
    pattern = "*",
    callback = require("user.theme").telescope_theme,
  })
end

