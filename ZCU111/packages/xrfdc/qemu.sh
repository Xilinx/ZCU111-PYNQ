#! /bin/bash

set -x
set -e

cd /root/xrfdc_build
make embeddedsw
make
make install

cd /root
rm -rf xrfdc_build
