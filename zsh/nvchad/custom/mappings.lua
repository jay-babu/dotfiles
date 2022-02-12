local map = require('core.utils').map

-- bufferline
map('n', 'gb', ':BufferLinePick<CR>')

-- truezen
map('n', '<leader>ta', ':TZAtaraxis <CR>')
map('n', '<leader>tm', ':TZMinimalist <CR>')
map('n', '<leader>tf', ':TZFocus <CR>')

-- toggleterm
map('n', '<c-\\>', ':ToggleTerm <CR>')
