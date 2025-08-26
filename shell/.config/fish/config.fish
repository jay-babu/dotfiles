bass source ~/.profile

set -x DONT_PROMPT_WSL_INSTALL true

set -x XDEB_PKGROOT ~/.config/xdeb

set sponge_delay 100

if status is-interactive
    # Commands to run in interactive sessions can go here

    # set -gx FZF_DEFAULT_OPTS '--hidden --preview "bat --style=numbers --color=always --line-range :500 {}"'

    function cd
        z $argv && eza -a -F --icons
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

    set -l encoded_password (echo $password | jq "@uri" -jRr)

    set -x -g DBUI_URL "postgres://$username:$password@$rds_endpoint:5432/$database_name"
    set -x -g DB_HOST "$rds_endpoint"
    set -x -g DBUI_URL_ENCODED "postgres://$username:$encoded_password@$rds_endpoint:5432/$database_name"
end

function dev_t
    for line in (aws configure export-credentials --profile Transformity --format env)
        set -l clean_line (string replace "export " "" $line)
        set -l parts (string split "=" $clean_line)
        if test (count $parts) -eq 2
            set -gx $parts[1] $parts[2]
        end
    end
    set -l account_number (aws sts get-caller-identity | jq -r ".Account")
    if echo $account_number | string match -q "165569969323"
        set -l database_name "postgres"
		echo "Gamma"
        set -x -g DATASOURCE_URL jdbc-secretsmanager:postgresql://transformity-gamma-cluster-cluster.cluster-cu3q2lrqndpl.us-east-1.rds.amazonaws.com:5432/postgres
        set -x -g DATASOURCE_USERNAME rds!cluster-f926b0ad-9c96-4830-a7ec-246892c81719
        set -e -g USER_REQUEST_LOCK_TABLE_NAME
        connect_to_rds $DATASOURCE_USERNAME "transformity-gamma-cluster-cluster.cluster-cu3q2lrqndpl.us-east-1.rds.amazonaws.com" $database_name
        pulumi login s3://transformity-pulumi-gamma
    else if echo $account_number | string match -q "928004597368"
		echo "Prod"
        set -x -g DATASOURCE_URL jdbc-secretsmanager:postgresql://transformity-production.cluster-c7q0uw4ubo4n.us-east-1.rds.amazonaws.com:5432/postgres
        set -x -g DATASOURCE_USERNAME rds!cluster-ed2fdf32-bf0a-420b-af63-0aafc8364dd7
        set -x -g USER_REQUEST_LOCK_TABLE_NAME drinks-pos-api-lock-table-c3dc622
        echo $DATASOURCE_USERNAME
        connect_to_rds $DATASOURCE_USERNAME "transformity-production.cluster-c7q0uw4ubo4n.us-east-1.rds.amazonaws.com" "postgres"
        pulumi login s3://transformity-pulumi-prod
    else if echo $account_number | string match -q "741448959376"
        echo "DNS"
        pulumi login s3://margin-pulumi-dns-management
    end
end

complete --command aws --no-files --arguments '(begin; set --local --export COMP_SHELL fish; set --local --export COMP_LINE (commandline); aws_completer | sed \'s/ $//\'; end)'

# tabtab source for packages
# uninstall by removing these lines
[ -f ~/.config/tabtab/fish/__tabtab.fish ]; and . ~/.config/tabtab/fish/__tabtab.fish; or true
[ -f ~/.config/fish/conf.d/tokyonight_storm.fish ]; and . ~/.config/fish/conf.d/tokyonight_storm.fish; or true
