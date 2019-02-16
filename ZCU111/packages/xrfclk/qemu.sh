#! /bin/bash

set -x
set -e

cd /root/xrfclk_build
make
make install

cd /root
rm -rf xrfclk_build
