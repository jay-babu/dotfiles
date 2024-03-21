return {
  "nvim-neotest/neotest",
  dependencies = {
    "nvim-lua/plenary.nvim",
    "nvim-treesitter/nvim-treesitter",
    "antoinemadec/FixCursorHold.nvim",
    "haydenmeade/neotest-jest",
    "nvim-neotest/neotest-go",
    "nvim-neotest/neotest-vim-test",
    "nvim-neotest/neotest-python",
    "vim-test/vim-test",
    "thenbe/neotest-playwright",
  },
  config = function()
    -- get neotest namespace (api call creates or returns namespace)
    local neotest_ns = vim.api.nvim_create_namespace "neotest"
    vim.diagnostic.config({
      virtual_text = {
        format = function(diagnostic)
          local message = diagnostic.message:gsub("\n", " "):gsub("\t", " "):gsub("%s+", " "):gsub("^%s+", "")
          return message
        end,
      },
    }, neotest_ns)
    require("neotest").setup {
      -- your neotest config here
      adapters = {
        require "neotest-python" {
          -- Extra arguments for nvim-dap configuration
          dap = { justMyCode = false },
        },
        require "neotest-go",
        require "neotest-vim-test" { allow_file_types = { "java" } },
        require "neotest-jest" {
          jestCommand = "npm test --",
          env = { CI = true },
          cwd = function(_) return vim.fn.getcwd() end,
        },
        require("neotest-playwright").adapter {
          options = {
            persist_project_selection = true,
            enable_dynamic_test_discovery = true,
          },
        },
      },
    }
  end,
}
