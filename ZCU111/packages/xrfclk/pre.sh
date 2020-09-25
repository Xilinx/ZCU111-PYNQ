#!/bin/bash

set -e
set -x

target=$1
script_dir="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

sudo cp -r $script_dir/pkg $target/root/xrfclk_build
cat $script_dir/boot.py | sudo tee -a $target/boot/boot.py
