#! /bin/bash

set -x
set -e

export BOARD=ZCU111
export PYNQ_JUPYTER_NOTEBOOKS=/home/xilinx/jupyter_notebooks

source /usr/local/share/pynq-venv/bin/activate

# Install RFSoC overlays
pip3 install https://github.com/Xilinx/SDFEC-PYNQ/releases/download/v2.0_$BOARD/rfsoc_sdfec-2.0-py3-none-any.whl --no-deps
pip3 install git+https://github.com/strath-sdr/rfsoc_qpsk@594268d --no-deps
pip3 install https://github.com/Xilinx/DSP-PYNQ/releases/download/v2.0_$BOARD/dsp_pynq-2.0-py3-none-any.whl --no-deps

# Install workshop notebooks
git clone https://github.com/Xilinx/PYNQ_RFSOC_Workshop.git --branch image_v2.6.0 pynq_rfsoc_workshop
make -C pynq_rfsoc_workshop install
rm -rf pynq_rfsoc_workshop
rm -rf "$PYNQ_JUPYTER_NOTEBOOKS/rfsoc_qpsk"

