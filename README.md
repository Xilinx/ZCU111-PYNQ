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
    [baremetal C drivers](https://github.com/Xilinx/embeddedsw/tree/5b3764e8eb42e543f411f6ec3ed31c7112c6e178/XilinxProcessorIPLib/drivers/rfdc).

  + xsdfec: A python driver for the SD-FEC blocks. This is a wrapper for the [baremetal C drivers](https://github.com/Xilinx/embeddedsw/tree/5b3764e8eb42e543f411f6ec3ed31c7112c6e178/XilinxProcessorIPLib/drivers/sd_fec).

  + xrfclk: A python driver for the onboard clock synthesizers. This is a
    wrapper around a lightly modified version of the
    [C example code](https://github.com/Xilinx/embeddedsw/blob/5b3764e8eb42e543f411f6ec3ed31c7112c6e178/XilinxProcessorIPLib/drivers/rfdc/examples/xrfdc_clk.c).

### Support

Please ask questions on the <a href="https://groups.google.com/forum/#!forum/pynq_project" target="_blank">PYNQ support forum</a>.

### Licenses

Please see the [LICENSE](LICENSE) file for how the repository and packages are licensed.
