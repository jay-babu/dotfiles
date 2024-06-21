return {
  {
    "AstroNvim/astrolsp",
    optional = true,
    ---@type AstroLSPOpts
    opts = {
      ---@diagnostic disable: missing-fields
      config = {
        yamlls = {
          schemas = require("schemastore").yaml.schemas(),
          validate = { enable = true },
        },
      },
    },
  },
}
