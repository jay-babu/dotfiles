---@type LazySpec
return {
  {
    "kristijanhusak/vim-dadbod-ui",
    optional = true,
    dev = true,
    specs = {
      {
        "AstroNvim/astrocore",
        opts = {
          options = {
            g = {
              completion_matching_ignore_case = 1,
            },
          },
        },
      },
    },
  },
}
