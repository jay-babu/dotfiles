local handle = io.popen("figlet -c 'Flying Raijin\nLevel 2'")
local result = ""
if handle ~= nil then
	result = handle:read("*a")
	handle:close()
end

return vim.fn.split(result, "\n")