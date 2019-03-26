# after building with Joe Britton's build-artiq.bash script, this will set up the kasli.
# M. Lichtman 2018-10-17

#set -e
#set -v

# for artiq 4:
artiq_flash -t kasli -V opticlock --srcbuild ~/artiq-dev/artiq/artiq_kasli
# for artiq 5:
#artiq_flash -t kasli -V opticlock --srcbuild True -d ~/artiq-dev/artiq/artiq_kasli

artiq_compile repository/idle_kernel.py
artiq_mkfs flash_storage.img -s rtio_clock e -s mac 00:0A:35:03:67:91 -s ip 192.168.1.98 -f idle_kernel repository/idle_kernel.elf
artiq_flash -t kasli -V opticlock -f flash_storage.img storage start

