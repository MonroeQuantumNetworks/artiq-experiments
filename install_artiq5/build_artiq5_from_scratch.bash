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
export NIX_PATH=~/.nix-defexpr/channels:$NIX_PATH
nix-channel --add https://nixbld.m-labs.hk/channel/custom/artiq/full/artiq-full
nix-channel --remove nixpkgs
nix-channel --add https://nixos.org/channels/nixos-19.03 nixpkgs
echo "substituters = https://cache.nixos.org https://nixbld.m-labs.hk
trusted-public-keys = cache.nixos.org-1:6NCHdD59X431o0gWypbMrAURkbJ16ZPMQFGspcDShjY= nixbld.m-labs.hk-1:5aSRVA5b320xbNvu30tqxVPXpld73bhtOeH6uAjRyHc=" > ~/.config/nix/nix.conf
nix-shell -p git
nix-shell -I artiqSrc=~/Documents/github/artiq-fork/artiq ~/Documents/github/nix-scripts/artiq-fast/shell-dev.nix

# compile the firmware with Vivado
cd ~/Documents/github/artiq-experiments
python -m artiq.gateware.targets.kasli.py -V monroe_ionphoton

# flash the firmware to the board
artiq_flash -t kasli -V monroe_ionphoton --srcbuild -d ./artiq_kasli
artiq_compile repository/idle_kernel.py
artiq_mkfs flash_storage.img -s rtio_clock e -s mac 00:0A:35:03:67:91 -s ip 192.168.1.98 -f idle_kernel repository/idle_kernel.elf
artiq_flash -t kasli -V monroe_ionphoton -f flash_storage.img --srcbuild -d ./artiq_kasli storage start
