if type -q bass
    bass source ~/.profile
end

set -x DONT_PROMPT_WSL_INSTALL true

set -x XDEB_PKGROOT ~/.config/xdeb

set sponge_delay 100

if status is-interactive
    functions --copy cd cd_wrapper

    # Commands to run in interactive sessions can go here

    # set -gx FZF_DEFAULT_OPTS '--hidden --preview "bat --style=numbers --color=always --line-range :500 {}"'

    function cd
        cd_wrapper $argv && eza -a -F --icons
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

function connect_to_rds_iam
    set rds_endpoint $argv[1]
    set database_name $argv[2]
    set db_user $argv[3]
    set aws_region $argv[4]
    set sslrootcert $argv[5]

    if test -z "$db_user"
        set db_user jay_hermes
    end

    if test -z "$aws_region"
        set aws_region us-east-1
    end

    if test -z "$sslrootcert"
        set sslrootcert /root/.aws/global-bundle.pem
    end

    set -l port 5432
    set -l token (aws rds generate-db-auth-token \
        --hostname $rds_endpoint \
        --port $port \
        --region $aws_region \
        --username $db_user)
    set -l encoded_token (printf "%s" "$token" | jq -sRr '@uri')

    set -x -g DB_HOST "$rds_endpoint"
    set -x -g DB_USER "$db_user"
    set -x -g AWS_REGION "$aws_region"
    set -x -g AWS_DEFAULT_REGION "$aws_region"

    set -x -g PGHOST "$rds_endpoint"
    set -x -g PGPORT "$port"
    set -x -g PGDATABASE "$database_name"
    set -x -g PGUSER "$db_user"
    set -x -g PGPASSWORD "$token"
    set -x -g PGSSLMODE verify-full
    set -x -g PGSSLROOTCERT "$sslrootcert"

    set -x -g DBUI_URL "postgres://$db_user@$rds_endpoint:$port/$database_name?sslmode=verify-full&sslrootcert=$sslrootcert"
    set -x -g DBUI_URL_ENCODED "postgres://$db_user:$encoded_token@$rds_endpoint:$port/$database_name?sslmode=verify-full&sslrootcert=$sslrootcert"
end

function dev_t
    aws configure export-credentials --profile $AWS_PROFILE --format fish | source
    set -l account_number (aws sts get-caller-identity | jq -r ".Account")
    if echo $account_number | string match -q "165569969323"
        set -l database_name "postgres"
		echo "Gamma"
        set -x -g DATASOURCE_URL jdbc-secretsmanager:postgresql://transformity-gamma-cluster-cluster.cluster-cu3q2lrqndpl.us-east-1.rds.amazonaws.com:5432/postgres?sslmode=verify-full&sslrootcert=src/main/resources/global-bundle.pem
        set -x -g DATASOURCE_USERNAME rds!cluster-99629e8b-3f13-4fc2-99c6-82d224376d93
        set -e -g USER_REQUEST_LOCK_TABLE_NAME
        connect_to_rds_iam "transformity-gamma-cluster-cluster.cluster-cu3q2lrqndpl.us-east-1.rds.amazonaws.com" $database_name
        pulumi login s3://transformity-pulumi-gamma
    else if echo $account_number | string match -q "928004597368"
		echo "Prod"
        set -x -g DATASOURCE_URL jdbc-secretsmanager:postgresql://transformity-production.cluster-c7q0uw4ubo4n.us-east-1.rds.amazonaws.com:5432/postgres?sslmode=verify-full&sslrootcert=src/main/resources/global-bundle.pem
        set -x -g DATASOURCE_USERNAME rds!cluster-ed2fdf32-bf0a-420b-af63-0aafc8364dd7
        set -x -g USER_REQUEST_LOCK_TABLE_NAME drinks-pos-api-lock-table-c3dc622
        echo $DATASOURCE_USERNAME
        connect_to_rds_iam "transformity-production.cluster-c7q0uw4ubo4n.us-east-1.rds.amazonaws.com" "postgres"
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

# bun
set --export BUN_INSTALL "$HOME/.bun"
set --export PATH $BUN_INSTALL/bin $PATH

if test -x ~/.local/bin/mise
    ~/.local/bin/mise activate fish | source
end

if type -q starship
    starship init fish | source
end
