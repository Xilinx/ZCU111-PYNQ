from setuptools import setup

setup(
   name = "xrfclk",
   version = '0.1',
   url = 'https://github.com/Xilinx/ZCU111-PYNQ/tree/master/ZCU111/packages/xrfclk',
   license = 'All rights reserved.',
   author = "Craig Ramsay",
   author_email = "cramsay01@gmail.com",
   packages = ['xrfclk'],
   package_data = {
   '' : ['*.py','*.so'],
   },
   install_requires=[
       'pynq',
   ],
   description = "Driver for the clock synthesizers on the ZCU111 board"
)
