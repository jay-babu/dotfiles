#!/usr/bin/env bash
set -euo pipefail

mkdir -p ~/code
cd ~/code || exit

git clone --recurse-submodules https://github.com/Transformity/CustomerDataUpload.git CustomerDataUpload
git clone https://github.com/Transformity/MasterPricingTableUploaderLambda.git MasterPricingTableUploaderLambda
git clone --recurse-submodules https://github.com/Transformity/POSBackend.git POSBackend
git clone --recurse-submodules https://github.com/Transformity/TransformityPOSFrontend.git TransformityPOSFrontend
git clone --recurse-submodules https://github.com/Transformity/phoenix.git phoenix
git clone https://github.com/Transformity/pos-db.git pos-db

mkdir -p bob
git clone --bare https://github.com/jay-babu/bob bob/.bare
printf 'gitdir: ./.bare\n' > bob/.git
git -C bob worktree add main main
git -C bob worktree add zeus-to-one-relationship-codegen zeus/to-one-relationship-codegen

mkdir -p zeus
git clone --bare https://github.com/Transformity/zeus zeus/.bare
printf 'gitdir: ./.bare\n' > zeus/.git
cat > zeus/.bare/hooks/post-checkout <<'EOF'
#!/usr/bin/env bash

set -euo pipefail

old_head="${1:-}"
is_branch_checkout="${3:-}"
null_ref="0000000000000000000000000000000000000000"

# git worktree add performs an initial checkout with a null old HEAD.
if [[ "$old_head" != "$null_ref" || "$is_branch_checkout" != "1" ]]; then
    exit 0
fi

printf 'zeus post-checkout: initializing submodules in %s\n' "$PWD" >&2
git submodule update --init --recursive

printf 'zeus post-checkout: running go generate work in %s\n' "$PWD" >&2
go generate work

EOF
chmod +x zeus/.bare/hooks/post-checkout
git -C zeus worktree add main main
