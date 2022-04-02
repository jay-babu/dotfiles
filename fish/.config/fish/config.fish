
fish_add_path (which brew)/.. 
fish_add_path (which brew)/../../opt/node@16/bin
fish_add_path (which brew)/../../opt/openjdk@11/bin
fish_add_path (which brew)/../../opt/nvim/bin
fish_add_path /home/linuxbrew/.linuxbrew/bin 
fish_add_path (go env GOPATH)/bin
# fish_add_path /home/linuxbrew/.linuxbrew/bin 
# fish_add_path /home/linuxbrew/.linuxbrew/opt/node@16/bin
# fish_add_path /home/linuxbrew/.linuxbrew/opt/openjdk@11/bin
# fish_add_path /home/linuxbrew/.linuxbrew/opt/nvim/bin
# fish_add_path "(go env GOPATH)"/bin

set -Ux DONT_PROMPT_WSL_INSTALL true

set -Ux EDITOR nvim

set -Ux XDEB_PKGROOT ~/.config/xdeb

if status is-interactive
    # Commands to run in interactive sessions can go here

    set -gx FZF_DEFAULT_OPTS '--hidden --preview "bat --style=numbers --color=always --line-range :500 {}"'

    function cd 
        builtin cd $argv && exa -a -F --icons
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
