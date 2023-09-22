# set brew_location (which brew)
# fish_add_path $brew_location/..
# fish_add_path $brew_location/../../opt/node@16/bin
# fish_add_path $brew_location/../../opt/openjdk@11/bin
# fish_add_path $brew_location/../../opt/nvim/bin
# fish_add_path /home/linuxbrew/.linuxbrew/bin
# fish_add_path (go env GOPATH)/bin

bass source ~/.profile

set -x DONT_PROMPT_WSL_INSTALL true

set -x XDEB_PKGROOT ~/.config/xdeb

set sponge_delay 100

if status is-interactive
    # Commands to run in interactive sessions can go here

    # set -gx FZF_DEFAULT_OPTS '--hidden --preview "bat --style=numbers --color=always --line-range :500 {}"'

    function cd
        builtin cd $argv && exa -a -F --icons
    end

    # Enable VI Mode
    fish_vi_key_bindings
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

function connect_to_rds
    set secret_id $argv[1]
    set rds_endpoint $argv[2]
    set database_name $argv[3]

    set -l username
    set -l secret_string (aws secretsmanager get-secret-value --secret-id $secret_id --query 'SecretString' --output text)
    set -l username (echo $secret_string | jq -r '.username')

    set -l password

    set -l password (echo $secret_string | jq -r '.password')

    set -x DBUI_URL "postgres://$username:$password@$rds_endpoint:5432/$database_name"

    # PGPASSWORD="$password" psql -h "$rds_endpoint" -U "$username" -d "$database_name" -w
end

function dev_t
    set -x DATASOURCE_URL jdbc-secretsmanager:postgresql://transformity-gamma.cluster-cu3q2lrqndpl.us-east-1.rds.amazonaws.com:5432/transformity_pos
    set -x DATASOURCE_USERNAME rds!cluster-cadc26c1-7647-4cd1-b34e-46d55017cfea
    connect_to_rds 'rds!cluster-cadc26c1-7647-4cd1-b34e-46d55017cfea' "transformity-gamma.cluster-cu3q2lrqndpl.us-east-1.rds.amazonaws.com" "transformity_pos"
end

complete --command aws --no-files --arguments '(begin; set --local --export COMP_SHELL fish; set --local --export COMP_LINE (commandline); aws_completer | sed \'s/ $//\'; end)'

# tabtab source for packages
# uninstall by removing these lines
[ -f ~/.config/tabtab/fish/__tabtab.fish ]; and . ~/.config/tabtab/fish/__tabtab.fish; or true
[ -f ~/.config/fish/conf.d/tokyonight_storm.fish ]; and . ~/.config/fish/conf.d/tokyonight_storm.fish; or true
