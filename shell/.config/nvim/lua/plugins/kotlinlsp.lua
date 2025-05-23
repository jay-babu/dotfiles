print "Loading Kotlin LSP config"
vim.print "Loading Kotlin LSP config"
---@type LazySpec
return {
  "AstroNvim/astrolsp",
  opts = function(
    _,
    ---@type AstroLSPOpts
    opts
  )
    opts.servers = opts.servers or {}
    table.insert(opts.servers, "kotlin_lsp")

    -- extend our configuration table to have our new prolog server
    opts.config = require("astrocore").extend_tbl(opts.config or {}, {
      -- this must be a function to get access to the `lspconfig` module
      kotlin_lsp = {
        cmd = { "kotlin-ls", "--stdio" },
        single_file_support = true,
        filetypes = { "kotlin" },
        root_markers = { "build.gradle", "build.gradle.kts", "pom.xml" },
      },
    })
  end,
}
