#!/usr/bin/env fish

brew install fish

if not command -v fisher &> /dev/null
    curl -sL https://git.io/fisher | source && fisher install jorgebucaran/fisher
end

fisher install jethrokuan/z IlanCosman/tide@v5 jhillyerd/plugin-git PatrickF1/fzf.fish edc/bass andreiborisov/sponge IlanCosman/tide@v5

