return {
    "folke/noice.nvim",
    event = "VeryLazy",
    opts = {
        lsp = {
            override = {
                ["vim.lsp.util.convert_input_to_markdown_lines"] = true,
                ["vim.lsp.util.stylize_markdown"] = true,
                ["cmp.entry.get_documentation"] = true,
            },
        },
        presets = {
            bottom_search = true, -- use a classic bottom cmdline for search
            command_palette = true, -- position the cmdline and popupmenu together
            long_message_to_split = true, -- long messages will be sent to a split
        },
    },
    keys = {
        {
            "<S-Enter>",
            function()
              require("noice").redirect(vim.fn.getcmdline())
            end,

            mode = "c",
            desc = "Redirect Cmdline",
        },
        {
            "<leader>snl",
            function()
              require("noice").cmd("last")
            end,
            desc = "Noice Last Message",
        },
        {
            "<leader>snh",
            function()
              require("noice").cmd("history")
            end,
            desc = "Noice History",
        },
        {
            "<leader>sna",

            function()
              require("noice").cmd("all")
            end,
            desc = "Noice All",
        },

        {

            "<c-f>",
            function()
              if not require("noice.lsp").scroll(4) then
                return "<c-f>zz"
              end
            end,
            silent = true,
            expr = true,
            desc = "Scroll forward",
            mode = { "i", "n", "s" },
        },
        {
            "<c-b>",
            function()
              if not require("noice.lsp").scroll( -4) then
                return "<c-b>zz"
              end
            end,
            silent = true,
            expr = true,
            desc = "Scroll backward",
            mode = { "i", "n", "s" },
        },
    },
}
