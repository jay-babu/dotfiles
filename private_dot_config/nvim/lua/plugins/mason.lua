local function exclude_gopls(_, opts)
  opts.ensure_installed = vim.tbl_filter(function(tool) return tool ~= "gopls" end, opts.ensure_installed or {})
end

return {
  {
    "mason-org/mason-lspconfig.nvim",
    opts = exclude_gopls,
  },
  {
    "WhoIsSethDaniel/mason-tool-installer.nvim",
    optional = true,
    opts = exclude_gopls,
  },
}
