#! /usr/bin/env nix-shell
#! nix-shell -i bash -I artiqSrc=/home/monroe/Documents/github/artiq-fork/artiq /home/monroe/Documents/github/nix-scripts/artiq-fast/shell-dev.nix

# compile the firmware with Vivado
cd ~/Documents/github/artiq-experiments
python -m artiq.gateware.targets.kasli.py -V monroe_ionphoton

# flash the firmware to the board
artiq_flash -t kasli -V monroe_ionphoton --srcbuild ./artiq_kasli
artiq_compile repository/idle_kernel.py
artiq_mkfs flash_storage.img -s rtio_clock e -s mac 00:0A:35:03:67:91 -s ip 192.168.1.98 -f idle_kernel repository/idle_kernel.elf
artiq_flash -t kasli -V monroe_ionphoton -f flash_storage.img --srcbuild ./artiq_kasli storage start
