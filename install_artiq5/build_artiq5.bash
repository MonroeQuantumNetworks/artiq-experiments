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

# October 2020
# From Drew/Manual

# Run this to build Entangler gateware
# nix-shell -I artiqSrc=/PATH/TO/ARTIQ/REPO/ /ENTANGLER/PATH/nix/entangler-shell-dev.nix --run "python -m entangler.kasli_generic /PATH/TO/KASLI_DESCRIPTOR.json"

# artiq_mkfs flashstorage_with_mac_and_ip.img -s ip 192.168.1.98 -s mac 00:0A:35:03:67:91
# artiq_flash -t kasli -V monroe_ionphoton -d ./artiq_kasli/ --srcbuild -f flashstorage_with_mac_and_ip.img

# artiq_mkfs flash_storage.img -s ip 192.168.1.98 -s mac 00:0A:35:03:67:91
# artiq_flash -t kasli -V monroe_ionphoton -d ./artiq_kasli/ --srcbuild -f flash_storage.img erase gateware bootloader firmware storage start
