# build source
# first you can disable unused hardware in ~/artiq-dev/artiq/artiq/gateware/targets/kasli.py:Opticlock.__init__ before building.  Also make sure to disable the corresponding hardware in ~Documents/github/artiq-experiments/opticlock/device_db.py
/usr/bin/time -o kasli_umd_ionphoton.time python ~/artiq-dev/artiq/artiq/gateware/targets/kasli.py --variant monroe_ionphoton


# UMD_IonPhoton_EEM
# EEM0 TTL InOut
# EEM1 TTL Out
# EEM (2, 3), (4, 5), (6, 7) Urukul
