return {
  "zbirenbaum/copilot.lua",
  opts = {
    -- Neovim's exit hooks cannot clean up the server after a crash or OOM kill.
    copilot_node_command = { "setpriv", "--pdeathsig", "KILL", "--", "node" },
  },
}
