
# setup the artiq source
rm -rf ~/Documents/github/artiq-fork
mkdir ~/Documents/github/artiq-fork
cd ~/Documents/github/artiq-fork
git clone --recursive https://github.com/MonroeQuantumNetworks/artiq.git
cd artiq
git checkout 5dev_MonroeIonPhoton
# set up the m-labs repository as upstream so we can keep the fork up to date
git remote add upstream https://github.com/m-labs/artiq.git
git fetch upstream

# setup the python environment with nix
export NIX_PATH=~/.nix-defexpr/channels:$NIX_PATH
cd ~/Documents/github
git clone --recursive https://git.m-labs.hk/m-labs/nix-scripts
nix-channel --add https://nixbld.m-labs.hk/channel/custom/artiq/full/artiq-full
nix-channel --remove nixpkgs
nix-channel --add https://nixos.org/channels/nixos-19.03 nixpkgs
echo "substituters = https://cache.nixos.org https://nixbld.m-labs.hk
trusted-public-keys = cache.nixos.org-1:6NCHdD59X431o0gWypbMrAURkbJ16ZPMQFGspcDShjY= nixbld.m-labs.hk-1:5aSRVA5b320xbNvu30tqxVPXpld73bhtOeH6uAjRyHc=" > ~/.config/nix/nix.conf
nix-shell -p git
nix-shell -I artiqSrc=~/Documents/github/artiq-fork/artiq ~/Documents/github/nix-scripts/artiq-fast/shell-dev.nix

# compile the firmware with Vivado
/usr/bin/time -o kasli_umd_ionphoton.time python ~/Documents/github/artiq-fork/artiq/artiq/gateware/targets/kasli.py --variant monroe_ionphoton

# flash the firmware to the board
artiq_flash -t kasli -V monroe_ionphoton -d ./artiq_kasli --srcbuild
artiq_compile repository/idle_kernel.py
artiq_mkfs flash_storage.img -s rtio_clock e -s mac 00:0A:35:03:67:91 -s ip 192.168.1.98 -f idle_kernel repository/idle_kernel.elf
artiq_flash -t kasli -V monroe_ionphoton -f flash_storage.img -d ./artiq_kasli --srcbuild storage start
