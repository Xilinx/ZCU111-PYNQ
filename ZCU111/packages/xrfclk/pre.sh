#!/bin/bash

set -e
set -x

target=$1
script_dir="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

sudo cp -r $script_dir/pkg $target/root/xrfclk_build
sudo cat $script_dir/boot.py >> $target/boot/boot.py
