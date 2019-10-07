#set -v

# run this from within the shell-dev.nix environment

# compile the firmware with Vivado
#cd ~/Documents/github/artiq-experiments
#rm -rf ~/Documents/github/artiq-experiments/artiq_kasli/monroe_ionphoton
#python -m artiq.gateware.targets.kasli_generic monroe_ionphoton.json

# flash the firmware to the board
artiq_flash -t kasli -V monroe_ionphoton --srcbuild -d ./artiq_kasli
artiq_compile repository/idle_kernel.py
artiq_mkfs flash_storage.img -s rtio_clock e -s mac 00:0A:35:03:67:91 -s ip 192.168.1.98 -f idle_kernel repository/idle_kernel.elf
artiq_flash -t kasli -V monroe_ionphoton -f flash_storage.img --srcbuild -d ./artiq_kasli storage start
