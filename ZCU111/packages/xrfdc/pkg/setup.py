from setuptools import setup

setup(
   name = "xrfdc",
   version = '0.1',
   url = 'https://github.com/Xilinx/ZCU111-PYNQ/tree/master/ZCU111/packages/xrfdc',
   license = 'All rights reserved.',
   author = "Craig Ramsay",
   author_email = "cramsay01@gmail.com",
   packages = ['xrfdc'],
   package_data = {
   '' : ['*.py','*.so','*.c'],
   },
   install_requires=[
       'pynq',
   ],
   description = "Driver for the RFSoC RF Data Converter IP"
)
