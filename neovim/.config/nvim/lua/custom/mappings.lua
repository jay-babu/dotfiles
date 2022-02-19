local map = require("core.utils").map

-- bufferline
map("n", "gb", ":BufferLinePick<CR>")

-- truezen
map("n", "<leader>ta", ":TZAtaraxis <CR>")
map("n", "<leader>tm", ":TZMinimalist <CR>")
map("n", "<leader>tf", ":TZFocus <CR>")

-- toggleterm
map("n", "<c-\\>", ":ToggleTerm <CR>")

-- lspconfig temp workaround
local utils = require("core.utils").load_config()
local maps = utils.mappings
local plugin_maps = maps.plugins.lspconfig

map("n", plugin_maps.hover, "<cmd>lua vim.lsp.buf.hover()<CR>")
map("n", plugin_maps.rename, "<cmd>lua vim.lsp.buf.rename()<CR>")
map("n", plugin_maps.references, "<cmd>lua vim.lsp.buf.references()<CR>")
map("n", plugin_maps.definition, "<cmd>lua vim.lsp.buf.definition()<CR>")
map("n", plugin_maps.code_action, "<cmd>lua vim.lsp.buf.code_action()<CR>")
map("n", plugin_maps.declaration, "<cmd>lua vim.lsp.buf.declaration()<CR>")
map("n", plugin_maps.set_loclist, "<cmd>lua vim.diagnostic.setloclist()<CR>")
map("n", plugin_maps.implementation, "<cmd>lua vim.lsp.buf.implementation()<CR>")
map("n", plugin_maps.signature_help, "<cmd>lua vim.lsp.buf.signature_help()<CR>")
map("n", plugin_maps.type_definition, "<cmd>lua vim.lsp.buf.type_definition()<CR>")
map("n", plugin_maps.float_diagnostics, "<cmd>lua vim.diagnostic.open_float()<CR>")
map("n", plugin_maps.add_workspace_folder, "<cmd>lua vim.lsp.buf.add_workspace_folder()<CR>")
map("n", plugin_maps.remove_workspace_folder, "<cmd>lua vim.lsp.buf.remove_workspace_folder()<CR>")
map("n", plugin_maps.goto_prev, '<cmd>lua vim.diagnostic.goto_prev({popup_opts={border="single"}})<CR>')
map("n", plugin_maps.goto_next, '<cmd>lua vim.diagnostic.goto_next({popup_opts={border="single"}})<CR>')
map("n", plugin_maps.list_workspace_folders, "<cmd>lua print(vim.inspect(vim.lsp.buf.list_workspace_folders()))<CR>")
