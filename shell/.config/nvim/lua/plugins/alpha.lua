return {
  "goolord/alpha-nvim",
  cmd = "Alpha",
  opts = function(_, dashboard)
    local handle = io.popen "figlet -c 'Flying Raijin\nLevel 2'"
    local result = ""
    if handle ~= nil then
      result = handle:read "*a"
      handle:close()
    end

    dashboard.section.header.val = vim.fn.split(result, "\n")

    return dashboard
  end,
}
