#! /bin/bash

set -x
set -e

export BOARD=ZCU111
export PYNQ_JUPYTER_NOTEBOOKS=/home/xilinx/jupyter_notebooks


###############################################################################
## Misc image setup

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
--- /usr/local/bin/start_pl_server.py	2019-02-21 20:28:58.537115574 +0000
+++ start_pl_server.py	2019-04-08 22:46:17.000000000 +0000
@@ -4,8 +4,10 @@
 import re
 import sys
 from pkg_resources import load_entry_point
+import xrfclk
 
 if __name__ == '__main__':
+    xrfclk.set_all_ref_clks(409.6)
     sys.argv[0] = re.sub(r'(-script\.pyw?|\.exe)?$', '', sys.argv[0])
     sys.exit(
         load_entry_point('pynq==2.4', 'console_scripts', 'start_pl_server.py')()
EOF

# Must build statsmodels from source (deb package is too old for plotly_express)
pip3 install --upgrade https://github.com/statsmodels/statsmodels/archive/v0.9.0.tar.gz

# We let statsmodels pull in new scipy/numpy packages for build time, but we can revert by
# uninstalling pip versions and falling back to the .deb packages
pip3 uninstall -y numpy scipy

# Freeze package versions to match v2.4 image
pip3 install Flask==1.0.2 jupyterlab==0.35.4 six==1.11.0 Werkzeug==0.14.1


###############################################################################
## Install RFSoC overlays

pip3 install https://github.com/Xilinx/SDFEC-PYNQ/releases/download/v1.0_$BOARD/rfsoc_sdfec-1.0-py3-none-any.whl
pip3 install git+https://github.com/strath-sdr/rfsoc_qpsk@51b6d97e
pip3 install https://github.com/Xilinx/DSP-PYNQ/releases/download/v1.0_$BOARD/dsp_pynq-1.0-py3-none-any.whl


###############################################################################
## Install Lab extensions

jupyter labextension install @jupyter-widgets/jupyterlab-manager@0.38 --no-build
jupyter labextension install plotlywidget@0.10.0 --no-build
jupyter labextension install @jupyterlab/plotly-extension@0.18 --no-build
jupyter lab build
rm -rf /usr/local/share/jupyter/lab/staging


###############################################################################
## Install workshop notebooks

git clone https://github.com/Xilinx/PYNQ_RFSOC_Workshop.git pynq_rfsoc_workshop
make -C pynq_rfsoc_workshop install
rm -rf pynq_rfsoc_workshop
rm -rf "$PYNQ_JUPYTER_NOTEBOOKS/rfsoc_qpsk"
