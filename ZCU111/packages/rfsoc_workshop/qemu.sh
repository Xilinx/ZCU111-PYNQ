#! /bin/bash

set -x
set -e

export BOARD=ZCU111
export PYNQ_JUPYTER_NOTEBOOKS=/home/xilinx/jupyter_notebooks

# Patch out cause of "require js" error in lab
patch --ignore-whitespace /usr/local/lib/python3.6/dist-packages/pynq/lib/pynqmicroblaze/magic.py  << 'EOF'
--- /usr/local/lib/python3.6/dist-packages/pynq/lib/pynqmicroblaze/magic.py	2019-02-21 20:26:36.000000000 +0000
+++ magic.py	2019-04-08 22:45:31.000000000 +0000
@@ -98,4 +98,4 @@
 if instance:
     get_ipython().register_magics(MicroblazeMagics)
-    display_javascript(js, raw=True)
+    #display_javascript(js, raw=True)
EOF

# Patch to have RF clock init on boot
patch --ignore-whitespace /usr/local/bin/start_pl_server.py  << 'EOF'
--- /usr/local/bin/start_pl_server.py	2020-09-23 17:49:12.133483000 +0100
+++ start_pl_server.py	2020-09-23 17:49:12.133483000 +0100
@@ -3,6 +3,8 @@
 import re
 import sys
 from pynq.pl_server.server import _start_server
+import xrfclk
 if __name__ == '__main__':
+    xrfclk.set_all_ref_clks(409.6)
     sys.argv[0] = re.sub(r'(-script\.pyw|\.exe)?$', '', sys.argv[0])
     sys.exit(_start_server())
EOF

# Install RFSoC overlays
pip3 install https://github.com/Xilinx/SDFEC-PYNQ/releases/download/v1.0_$BOARD/rfsoc_sdfec-1.0-py3-none-any.whl
pip3 install git+https://github.com/strath-sdr/rfsoc_qpsk@913169d --no-deps
pip3 install https://github.com/Xilinx/DSP-PYNQ/releases/download/v1.0_$BOARD/dsp_pynq-1.0-py3-none-any.whl

# Install workshop notebooks
git clone https://github.com/Xilinx/PYNQ_RFSOC_Workshop.git pynq_rfsoc_workshop
make -C pynq_rfsoc_workshop install
rm -rf pynq_rfsoc_workshop
rm -rf "$PYNQ_JUPYTER_NOTEBOOKS/rfsoc_qpsk"

