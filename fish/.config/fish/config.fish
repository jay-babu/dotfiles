fish_add_path /home/linuxbrew/.linuxbrew/bin 
fish_add_path /home/linuxbrew/.linuxbrew/opt/node@16/bin
fish_add_path /home/linuxbrew/.linuxbrew/opt/openjdk@11/bin
fish_add_path /home/linuxbrew/.linuxbrew/opt/nvim/bin
fish_add_path "(go env GOPATH)"/bin

set -gx DONT_PROMPT_WSL_INSTALL true

set -gx EDITOR nvim

if status is-interactive
    # Commands to run in interactive sessions can go here

    set -gx FZF_DEFAULT_OPTS '--hidden --preview "bat --style=numbers --color=always --line-range :500 {}"'

    function cd 
        builtin cd $argv && exa -a
    end
end

function ...
  ../..
end
function ....
  ../../..
end
function .....
  ../../../..
end
