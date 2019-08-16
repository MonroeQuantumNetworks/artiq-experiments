#export NIX_PATH=~/.nix-defexpr/channels
nix-shell -I artiqSrc=~/Documents/github/artiq-fork/artiq ~/Documents/github/nix-scripts/artiq-fast/shell-dev.nix
#export PYTHONPATH=~/Documents/github/artiq-fork/artiq:${PYTHONPATH}
#cd ~/Documents/github/artiq-experiments
