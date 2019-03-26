# setup artiq 4

artiq_flash -t kasli -V opticlock --srcbuild ~/artiq-4.0/artiq/artiq_kasli
artiq_compile repository/idle_kernel.py
artiq_mkfs flash_storage.img -s rtio_clock e -s mac 00:0A:35:03:67:91 -s ip 192.168.1.98 -f idle_kernel repository/idle_kernel.elf
artiq_flash -t kasli -V opticlock -f flash_storage.img storage start
#artiq_coremgmt config write -f idle_kernel repository/idle_kernel.elf
#artiq_coremgmt config write -s rtio_clock e
