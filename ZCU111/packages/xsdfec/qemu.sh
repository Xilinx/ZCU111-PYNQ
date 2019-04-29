#! /bin/bash

set -x
set -e

cd /root/xsdfec_build
make embeddedsw
make
make install

cd /root
rm -rf xsdfec_build
