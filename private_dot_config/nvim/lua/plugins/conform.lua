return {
  "stevearc/conform.nvim",
  opts = function(_, opts)
    opts.formatters_by_ft.go = { "goimports", "gofumpt", lsp_format = "never" }

    local upstream_format_on_save = opts.format_on_save
    opts.format_on_save = function(bufnr)
      local format_opts = upstream_format_on_save
      if type(format_opts) == "function" then format_opts = format_opts(bufnr) end
      if not format_opts then return end
      if vim.bo[bufnr].filetype == "go" then
        format_opts = vim.tbl_extend("force", {}, format_opts, { lsp_format = "never" })
      end
      return format_opts
    end
  end,
}
