## PYNQ Board Repository for the Zynq UltraScale+ RFSoC ZCU111
This repository contains source files and instructions for building PYNQ to run on the 
[ZCU111 board](https://www.xilinx.com/products/boards-and-kits/zcu111.html).

### ZCU111 Board Files

Clone this repo, download the ZCU111 petalinux BSP from [here](https://www.xilinx.com/support/download/index.html/content/xilinx/en/downloadNav/embedded-design-tools.html), and place it in the ZCU111 folder.

You can then build the image from the PYNQ repo's sdbuild folder with
```
make BOARDDIR=~/where/you/cloned/this/repo/to
```

### RFSoC PYNQ Packages

  + xrfdc: A python driver for the RF Data Converters. This is a wrapper for the
    [baremetal C drivers](https://github.com/Xilinx/embeddedsw/tree/23eb39df101391b896adf20fa9d6c5aee27b0adc/XilinxProcessorIPLib/drivers/rfdc).

  + xrfclk: A python driver for the onboard clock synthesizers. This is a
    wrapper around a lightly modified version of the
    [C example code](https://github.com/Xilinx/embeddedsw/blob/23eb39df101391b896adf20fa9d6c5aee27b0adc/XilinxProcessorIPLib/drivers/rfdc/examples/xrfdc_clk.c).

### Support

Please ask questions on the <a href="https://groups.google.com/forum/#!forum/pynq_project" target="_blank">PYNQ support forum</a>.

### Licenses

Please see the [LICENSE](LICENSE) file for how the repository and packages are licensed.
