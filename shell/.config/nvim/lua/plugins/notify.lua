return {
  "rcarriga/nvim-notify",
  optional = true,
  init = function() require("astrocore").load_plugin_with_func("nvim-notify", vim, "notify") end,
  opts = {
    background_colour = "#000000",
  },
}
