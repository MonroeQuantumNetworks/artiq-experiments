set -v
# This file overwrites the source code.  It is not generally necessary to re-run this.

# Download the forked source code repository.
rm -rf ~/Documents/github/artiq-fork
mkdir ~/Documents/github/artiq-fork
cd ~/Documents/github/artiq-fork
git clone --recursive http://github.com/MonroeQuantumNetworks/artiq.git
cd artiq
git checkout 5dev_MonroeIonPhoton
# set up the m-labs repository as upstream so we can keep the fork up to date
git remote add upstream https://github.com/m-labs/artiq.git
git fetch upstream

# create the nix shell
rm -rf ~/Documents/github/nix-scripts
cd ~/Documents/github
git clone --recursive https://git.m-labs.hk/m-labs/nix-scripts
export NIX_PATH=~/.nix-defexpr/channels
nix-channel --add https://nixbld.m-labs.hk/channel/custom/artiq/full/artiq-full
nix-channel --remove nixpkgs
nix-channel --add https://nixos.org/channels/nixos-19.03 nixpkgs
nix-channel --update
echo "substituters = https://cache.nixos.org https://nixbld.m-labs.hk
trusted-public-keys = cache.nixos.org-1:6NCHdD59X431o0gWypbMrAURkbJ16ZPMQFGspcDShjY= nixbld.m-labs.hk-1:5aSRVA5b320xbNvu30tqxVPXpld73bhtOeH6uAjRyHc=" > ~/.config/nix/nix.conf
cd ~/Documents/github/artiq-experiments
