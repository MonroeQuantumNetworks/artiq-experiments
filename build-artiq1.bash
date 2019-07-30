#!/bin/bash
set -e
set -v

pushd .
source activate base
conda env remove -n artiq-dev --yes --quiet

rm -rf ~/Documents/github/artiq-fork
mkdir ~/Documents/github/artiq-fork
cd ~/Documents/github/artiq-fork

git clone --recursive https://github.com/MonroeQuantumNetworks/artiq.git
cd artiq
# MTL 2019-07-30
# changed from "git checkout $1" so that we get the Monroe specific version of the release-4.0 branch, instead of the latest master branch which is artiq-dev 5.0.
git checkout 4.0_MonroeIonPhoton

conda env create -f conda/artiq-dev.yaml
source activate artiq-dev
conda install cython --yes --quiet
pip install -e .

# now run build-artiq2.bash to build the firmware
