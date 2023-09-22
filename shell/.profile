# ~/.profile: executed by the command interpreter for login shells.
# This file is not read by bash(1), if ~/.bash_profile or ~/.bash_login
# exists.
# see /usr/share/doc/bash/examples/startup-files for examples.
# the files are located in the bash-doc package.

# the default umask is set in /etc/profile; for setting the umask
# for ssh logins, install and configure the libpam-umask package.
#umask 022

# if running bash
if [ -n "$BASH_VERSION" ]; then
	# include .bashrc if it exists
	if [ -f "$HOME/.bashrc" ]; then
		. "$HOME/.bashrc"
	fi
fi

if [ -f "$HOME/.config/.customrc" ]; then
	source "$HOME/.config/.customrc"
fi

# set PATH so it includes user's private bin if it exists
if [ -d "$HOME/bin" ]; then
	PATH="$HOME/bin:$PATH"
fi

# set PATH so it includes user's private bin if it exists
if [ -d "$HOME/.local/bin" ]; then
	PATH="$HOME/.local/bin:$PATH"
fi

# set PATH so it includes user's private bin if it exists
if [ -d "$HOME/.cargo/bin" ]; then
	PATH="$HOME/.cargo/bin:$PATH"
fi

# set PATH so it includes user's private bin if it exists
if [ -d "$HOME/go/bin" ]; then
	PATH="$HOME/go/bin:$PATH"
fi

# set PATH so it includes user's private bin if it exists
if [ -d "$HOME/.local/share/gem/ruby/3.0.0/bin" ]; then
	PATH="$HOME/.local/share/gem/ruby/3.0.0/bin:$PATH"
fi

function connect_to_rds() {
	local secret_id="$1"
	local rds_endpoint="$2"
	local database_name="$3"

	local username
	local secret_string
	secret_string=$(aws secretsmanager get-secret-value --secret-id "$secret_id" --query 'SecretString' --output text)
	username=$(echo "$secret_string" | jq -r '.username')
	local password
	password=$(echo "$secret_string" | jq -r '.password')

	export DBUI_URL="postgres://$username:$password@$rds_endpoint:5432/$database_name"

	# PGPASSWORD="$password" psql -h "$rds_endpoint" -U "$username" -d "$database_name" -w
}

function dev_t() {
	export DATASOURCE_URL=jdbc-secretsmanager:postgresql://transformity-gamma.cluster-cu3q2lrqndpl.us-east-1.rds.amazonaws.com:5432/transformity_pos
	export DATASOURCE_USERNAME=rds!cluster-cadc26c1-7647-4cd1-b34e-46d55017cfea
	connect_to_rds 'rds!cluster-cadc26c1-7647-4cd1-b34e-46d55017cfea' "transformity-gamma.cluster-cu3q2lrqndpl.us-east-1.rds.amazonaws.com" "transformity_pos"
}

alias v="nvim"
export EDITOR="nvim"
export BROWSER="wslview"

export DESKTOP_SESSION="bspwm"
