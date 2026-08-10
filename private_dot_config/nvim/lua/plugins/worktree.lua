return {
  {
    "polarmutex/git-worktree.nvim",
    version = "^2",
    dependencies = { "nvim-lua/plenary.nvim" },
    keys = {
      {
        "<Leader>Ww",
        function()
          local result = vim.system({ "git", "worktree", "list", "--porcelain" }, { text = true }):wait()
          if result.code ~= 0 then
            vim.notify(result.stderr, vim.log.levels.ERROR, { title = "git-worktree" })
            return
          end

          local worktrees = {}
          for path in result.stdout:gmatch "worktree ([^\n]+)" do
            table.insert(worktrees, path)
          end
          vim.ui.select(worktrees, { prompt = "Switch worktree" }, function(path)
            if path then require("git-worktree").switch_worktree(path) end
          end)
        end,
        desc = "Switch worktree",
      },
      {
        "<Leader>Wc",
        function()
          vim.ui.input({ prompt = "Worktree path: " }, function(path)
            if not path or path == "" then return end
            vim.ui.input({ prompt = "Branch (empty for detached): " }, function(branch)
              if branch ~= nil then require("git-worktree").create_worktree(path, branch) end
            end)
          end)
        end,
        desc = "Create worktree",
      },
    },
  },
}
