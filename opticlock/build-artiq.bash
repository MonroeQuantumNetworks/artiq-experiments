#!/bin/bash
set -e
set -v

pushd .
source activate base
conda env remove -n artiq-dev --yes --quiet
rm -rf ~/artiq-dev

mkdir ~/artiq-dev
cd ~/artiq-dev

git clone --recursive http://github.com/m-labs/artiq
cd artiq
# MTL 2019-03-22
# changed from "git checkout $1" so that we get the release-4.0 branch, instead of the latest artiq-dev 5.0 branch
git checkout tags/4.0

conda env create -f conda/artiq-dev.yaml 
source activate artiq-dev
#git apply  ~/github/jbqubit/sinara-testing/sayma/tools/bypass_hmc830.diff
#conda install --force --yes --quiet jesd204b=0.6
conda install cython --yes --quiet 
pip install -e .


# MTL 2019-03-22
# Uncomment this to build source.  I commented it out so I can disable unused hardware in ~artiq-dev/artiq/gateware/targets/kasli.py:Opticlock.__init__ before building.  Also make sure to disable the corresponding hardware in ~Documents/github/artiq-experiments/opticlock/device_db.py
#/usr/bin/time -o kasli_opticlock.time python artiq/gateware/targets/kasli.py --variant opticlock


# opticlock
# EEM0 TTL
# EEM1 TTL
# EEM2 TTL
# EEM3 Nogogorny
# EEM5, EEM4 Urukul
# EEM6 Urukul
# EEM7 Zotino
