# ~/.profile: executed by the command interpreter for login shells.
# This file is not read by bash(1), if ~/.bash_profile or ~/.bash_login
# exists.
# see /usr/share/doc/bash/examples/startup-files for examples.
# the files are located in the bash-doc package.

# the default umask is set in /etc/profile; for setting the umask
# for ssh logins, install and configure the libpam-umask package.
#umask 022

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

PATH=$(echo "$PATH" | tr ':' '\n' | grep -v -e '/mnt/c/Windows/system32' -e '/mnt/c/Windows/System32/Wbem' | tr '\n' ':')

alias v="nvim"
alias lg="lazygit"
export EDITOR="nvim"
export BROWSER="wslview"
export spring_profiles_active="local"
export STRIPE_API_KEY="sk_test_51Oe0IbDCuRuHsY0oAHrWqh0uwlB25jaDojYIAPb9mNSApEO2xagYGS3jBzvtsI2rKKOFFbcw085p06h1z0kfgWOE00XLGFMku5"
export AWS_PROFILE="Transformity"
export AWS_REGION="us-east-1"

# Add easy way to navigate to /mnt/g/My Drive/Store Exports/Data/
export STORE_DATA="/mnt/g/My Drive/Store Exports/Data/"

export NVM_DIR="$([ -z "${XDG_CONFIG_HOME-}" ] && printf %s "${HOME}/.nvm" || printf %s "${XDG_CONFIG_HOME}/nvm")"
[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh" # This loads nvm
. "$HOME/.cargo/env"
