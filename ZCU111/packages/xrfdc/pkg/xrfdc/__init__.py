#   Copyright (c) 2018, Xilinx, Inc.
#   All rights reserved.
#
#   Redistribution and use in source and binary forms, with or without
#   modification, are permitted provided that the following conditions are met:
#
#   1.  Redistributions of source code must retain the above copyright notice,
#       this list of conditions and the following disclaimer.
#
#   2.  Redistributions in binary form must reproduce the above copyright
#       notice, this list of conditions and the following disclaimer in the
#       documentation and/or other materials provided with the distribution.
#
#   3.  Neither the name of the copyright holder nor the names of its
#       contributors may be used to endorse or promote products derived from
#       this software without specific prior written permission.
#
#   THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
#   AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO,
#   THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
#   PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR
#   CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
#   EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
#   PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS;
#   OR BUSINESS INTERRUPTION). HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY,
#   WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR
#   OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF
#   ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

__author__ = "Peter Ogden"
__copyright__ = "Copyright 2018, Xilinx"
__email__ = "pynq_support@xilinx.com"


import cffi
import os
import pynq
import warnings
from wurlitzer import sys_pipes

_THIS_DIR = os.path.dirname(__file__)

with open(os.path.join(_THIS_DIR, 'xrfdc_functions.c'), 'r') as f:
    header_text = f.read()

_ffi = cffi.FFI()
_ffi.cdef(header_text)

_lib = _ffi.dlopen(os.path.join(_THIS_DIR, 'libxrfdc.so'))


# Next stage is a simple wrapper function which checks the existance of the
# function in the library and the return code and throws an exception if either
# fails.

def _safe_wrapper(name, *args, **kwargs):
    with sys_pipes():
        if not hasattr(_lib, name):
            raise RuntimeError(f"Function {name} not in library")
        if getattr(_lib, name)(*args, **kwargs):
            raise RuntimeError(f"Function {name} call failed")


# To reduce the amount of typing we define the properties we want for each
# class in the hierarchy. Each element of the array is a tuple consisting of
# the property name, the type of the property and whether or not it is
# read-only. These should match the specification of the C API but without the
# `XRFdc_` prefix in the case of the function name.

_block_props = [("BlockStatus", "XRFdc_BlockStatus", True),
                ("MixerSettings", "XRFdc_Mixer_Settings", False),
                ("QMCSettings", "XRFdc_QMC_Settings", False),
                ("CoarseDelaySettings", "XRFdc_CoarseDelay_Settings", False),
                ("NyquistZone", "u32", False),
                ("FabRdVldWords", "u32", True),
                ("FabWrVldWords", "u32", True)]

_adc_props = [("DecimationFactor", "u32", False),
              ("ThresholdClearMode", "u32", False),
              ("ThresholdSettings", "XRFdc_Threshold_Settings", False),
              ("CalibrationMode", "u8", False)]

_dac_props = [("InterpolationFactor", "u32", False),
              ("DecoderMode", "u32", False),
              ("OutputCurr", "int", True),
              ("InvSincFIR", "u16", False)]

_tile_props = [("FabClkOutDiv", "u16", False),
               ("FIFOStatus", "u8", True),
               ("ClockSource", "u32", True),
               ("PLLLockStatus", "u32", True)]

_rfdc_props = [("IPStatus", "XRFdc_IPStatus", True)]

# Next we define some helper functions for creating properties and
# packing/unpacking Python types into C structures

class PropertyDict(dict):
    """Subclass of dict to support update callbacks to C driver"""
    def __init__(self, *args, **kwargs):
        self.callback = lambda _:0
        self.update(*args, **kwargs)

    def set_callback(self, callback):
        """Set the callback function triggered on __setitem__""" 
        self.callback = callback

    def __setitem__(self, key, val):
        dict.__setitem__(self, key, val)
        self.callback(self)


def _pack_value(typename, value):
    if isinstance(value, dict):
        c_value = _ffi.new(f"{typename}*")
        for k, v in value.items():
            setattr(c_value, k, v)
        value = c_value
    return value


def _unpack_value(typename, value):
    if dir(value):
        return PropertyDict({k: getattr(value, k) for k in dir(value)}) # Struct
    else:
        return value[0] # Scalar

# The underlying C functions for generic behaviour (applies to both DAC
# and ADC blocks) expect an argument for the type of block used.
# Other functions leave the type of block implicit. We handle this distinction
# by bubbling up through either `_call_function` or `_call_function_implicit`
# calls. 


def _create_c_property(name, typename, readonly, implicit_type=False):
    def _get(self):
        value = _ffi.new(f"{typename}*")
        c_func = self._call_function if not implicit_type else \
                 self._call_function_implicit
        c_func(f"Get{name}", value)
        value = _unpack_value(typename, value)
        if isinstance(value, PropertyDict):
            value.set_callback(lambda value: c_func(
                f"Set{name}", _pack_value(typename, value)))
        return value

    def _set(self, value):
        if not implicit_type:
            self._call_function(f"Set{name}", _pack_value(typename, value))
        else:
            self._call_function_implicit(f"Set{name}", _pack_value(typename, value))

    if readonly:
        return property(_get)
    else:
        return property(_get, _set)

# Finally we can define the object hierarchy. Each element of the object
# hierarchy has a `_call_function` method which handles adding the
# block/tile/toplevel arguments to the list of function parameters.


class RFdcBlock:
    def __init__(self, parent, index):
        self._parent = parent
        self._index = index

    def _call_function(self, name, *args):
        return self._parent._call_function(name, self._index, *args)
    
    def ResetNCOPhase(self):
        self._call_function("ResetNCOPhase")

    def UpdateEvent(self, Event):
        self._call_function("UpdateEvent", Event)


class RFdcDacBlock(RFdcBlock):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def _call_function_implicit(self, name, *args):
        return self._parent._call_function_implicit(name, self._index, *args)


class RFdcAdcBlock(RFdcBlock):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def _call_function_implicit(self, name, *args):
        return self._parent._call_function_implicit(name, self._index, *args)

    def ThresholdStickyClear(self, ThresholdToUpdate):
        self._call_function_implicit("ThresholdStickyClear", ThresholdToUpdate)


class RFdcTile:
    def __init__(self, parent, index):
        self._index = index
        self._parent = parent

    def _call_function(self, name, *args):
        return self._parent._call_function(name, self._type, self._index, *args)

    def _call_function_implicit(self, name, *args):
        return self._parent._call_function(name, self._index, *args)

    def StartUp(self):
        self._call_function("StartUp")

    def ShutDown(self):
        self._call_function("Shutdown")

    def Reset(self):
        self._call_function("Reset")
    
    def SetupFIFO(self, Enable):
        self._call_function("SetupFIFO", Enable)

    def DumpRegs(self):
        self._call_function("DumpRegs")

    def DynamicPLLConfig(self, source, ref_clk_freq, samp_rate):
        self._call_function("DynamicPLLConfig", source, ref_clk_freq, samp_rate)


class RFdcDacTile(RFdcTile):
    def __init__(self, *args):
        super().__init__(*args)
        self._type = _lib.XRFDC_DAC_TILE
        self.blocks = [RFdcDacBlock(self, i) for i in range(4)]


class RFdcAdcTile(RFdcTile):
    def __init__(self, *args):
        super().__init__(*args)
        self._type = _lib.XRFDC_ADC_TILE
        self.blocks = [RFdcAdcBlock(self, i) for i in range(4)]


class RFdc(pynq.DefaultIP):
    bindto = ["xilinx.com:ip:usp_rf_data_converter:2.3"]

    def __init__(self, description):
        super().__init__(description)
        if 'parameters' in description:
            from .config import populate_config
            self._config = _ffi.new('XRFdc_Config*')
            populate_config(self._config, description['parameters'])
            pass
        else:
            warnings.warn("Please use an hwh file with the RFSoC driver"
                          " - the default configuration is being used")
            self._config = _lib.XRFdc_LookupConfig(0)
        self._instance = _ffi.new("XRFdc*")
        self._config.BaseAddr = self.mmio.array.ctypes.data
        _lib.XRFdc_CfgInitialize(self._instance, self._config)
        self.adc_tiles = [RFdcAdcTile(self, i) for i in range(4)]
        self.dac_tiles = [RFdcDacTile(self, i) for i in range(4)]

    def _call_function(self, name, *args):
        _safe_wrapper(f"XRFdc_{name}", self._instance, *args)


# Finally we can add our data-driven properties to each class in the hierarchy

for (name, typename, readonly) in _block_props:
    setattr(RFdcBlock, name, _create_c_property(name, typename, readonly))

for (name, typename, readonly) in _adc_props:
    setattr(RFdcAdcBlock, name, _create_c_property(name, typename, readonly, implicit_type=True))

for (name, typename, readonly) in _dac_props:
    setattr(RFdcDacBlock, name, _create_c_property(name, typename, readonly, implicit_type=True))

for (name, typename, readonly) in _tile_props:
    setattr(RFdcTile, name, _create_c_property(name, typename, readonly))

for (name, typename, readonly) in _rfdc_props:
    setattr(RFdc, name, _create_c_property(name, typename, readonly))

# Some of our more important #define constants
CLK_SRC_PLL = 0x1
CLK_SRC_EXT = 0x2

EVNT_SRC_IMMEDIATE = 0x00000000
EVNT_SRC_SLICE     = 0x00000001
EVNT_SRC_TILE      = 0x00000002
EVNT_SRC_SYSREF    = 0x00000003
EVNT_SRC_MARKER    = 0x00000004
EVNT_SRC_PL        = 0x00000005
EVENT_MIXER        = 0x00000001
EVENT_CRSE_DLY     = 0x00000002
EVENT_QMC          = 0x00000004

MIXER_MODE_OFF = 0x0
MIXER_MODE_C2C = 0x1
MIXER_MODE_C2R = 0x2
MIXER_MODE_R2C = 0x3
MIXER_MODE_R2R = 0x4

MIXER_TYPE_COARSE = 0x1
MIXER_TYPE_FINE   = 0x2
MIXER_TYPE_OFF    = 0x3

COARSE_MIX_OFF                     = 0x0
COARSE_MIX_SAMPLE_FREQ_BY_TWO      = 0x2
COARSE_MIX_SAMPLE_FREQ_BY_FOUR     = 0x4
COARSE_MIX_MIN_SAMPLE_FREQ_BY_FOUR = 0x8
COARSE_MIX_BYPASS                  = 0x10

MIXER_SCALE_AUTO = 0x0
MIXER_SCALE_1P0  = 0x1
MIXER_SCALE_0P7  = 0x2

FAB_CLK_DIV1   = 0x1
FAB_CLK_DIV2   = 0x2
FAB_CLK_DIV4   = 0x3
FAB_CLK_DIV8   = 0x4
FAB_CLK_DIV16  = 0x5
