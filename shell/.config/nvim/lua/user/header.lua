local handle = io.popen("figlet -c 'Flying Raijin\nLevel 2'")
local result = ""
if handle ~= nil then
	result = handle:read("*a")
	handle:close()
end

return astronvim.user_plugin_opts("header", vim.fn.split(result, "\n"), nil, "work")
