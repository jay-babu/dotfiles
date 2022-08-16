# set brew_location (which brew)
# fish_add_path $brew_location/.. 
# fish_add_path $brew_location/../../opt/node@16/bin
# fish_add_path $brew_location/../../opt/openjdk@11/bin
# fish_add_path $brew_location/../../opt/nvim/bin
# fish_add_path /home/linuxbrew/.linuxbrew/bin 
# fish_add_path (go env GOPATH)/bin

bass source ~/.profile

set -Ux DONT_PROMPT_WSL_INSTALL true

set -Ux EDITOR nvim

set -Ux XDEB_PKGROOT ~/.config/xdeb

set sponge_delay 100

if status is-interactive
    # Commands to run in interactive sessions can go here

    # set -gx FZF_DEFAULT_OPTS '--hidden --preview "bat --style=numbers --color=always --line-range :500 {}"'

    function cd 
        builtin cd $argv && exa -a -F --icons
    end
end

# Start X at login
if status is-login
    if test -z "$DISPLAY" -a "$XDG_VTNR" = 1
        exec startx -- -keeptty
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

# tabtab source for packages
# uninstall by removing these lines
[ -f ~/.config/tabtab/fish/__tabtab.fish ]; and . ~/.config/tabtab/fish/__tabtab.fish; or true
