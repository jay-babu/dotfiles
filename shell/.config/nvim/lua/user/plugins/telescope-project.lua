astronvim.which_key_register({
  n = {
    ["<leader>"] = {
      f = {
        ["p"] = { ":lua require'telescope'.extensions.project.project{}<CR>", "Telescope Projects" },
      },
    },
  },
})
require("telescope").load_extension("project")
