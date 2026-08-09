---@type LazySpec
return {
  {
    "AlexandrosAlexiou/kotlin.nvim",
    ft = { "kotlin" },
    dependencies = { "oil.nvim", "trouble.nvim" },
    config = function()
      local kotlin_lsp_dir = vim.fn.system { "/root/.local/bin/mise", "where", "http:kotlin-lsp" }
      if vim.v.shell_error == 0 then vim.env.KOTLIN_LSP_DIR = vim.trim(kotlin_lsp_dir) end

      require("kotlin").setup {
        root_markers = {
          { "settings.gradle", "settings.gradle.kts", "mvnw", "mvnw.cmd", ".git" },
          { "build.gradle", "build.gradle.kts", "pom.xml" },
        },
        jdk_for_symbol_resolution = os.getenv "JAVA_HOME",
        -- Large enough for multi-module projects without reserving 16 GiB for every Kotlin workspace.
        jvm_args = { "-Xmx4g" },
        inlay_hints = {
          enabled = true,
          parameters = true,
          parameters_compiled = true,
          parameters_excluded = false,
          types_property = true,
          types_variable = true,
          function_return = true,
          function_parameter = true,
          lambda_return = true,
          lambda_receivers_parameters = true,
          value_ranges = true,
          kotlin_time = true,
        },
      }
    end,
  },
}
