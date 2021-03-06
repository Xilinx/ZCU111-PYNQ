#   Copyright (c) 2019, Xilinx, Inc.
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

import cffi
import os
import pynq
import warnings
import parsec as ps
import weakref
from wurlitzer import sys_pipes

__author__    = "Craig Ramsay"
__copyright__ = "Copyright 2019, Xilinx"
__email__     = "pynq_support@xilinx.com"


# The HWH file includes a lot of information about all of the available code
# parameters. This includes nested lists, etc. so we use [parser
# combinators](https://en.wikipedia.org/wiki/Parsec_(parser)) to keep this
# managable.


_whitespace = ps.regex(r'\s*')
_lexeme = lambda p: p << _whitespace

_lbrace      = _lexeme(ps.string('{'))
_rbrace      = _lexeme(ps.string('}'))
_separator   = _lexeme(ps.regex(r'[ ,]'))
_name        = _lexeme(ps.regex(r'[\w]+'))
_num_hex     = _lexeme(ps.regex(r'0x[0-9a-fA-F]+')).parsecmap(lambda h: int(h, base=16))
_num_int     = _lexeme(ps.regex(r'-?(0|[1-9][0-9]*)([.][0-9]+)?([eE][+-]?[0-9]+)?')).parsecmap(int)
_num_float   = _lexeme(ps.regex(r'-?(0|[1-9][0-9]*)([.][0-9]+)?([eE][+-]?[0-9]+)?')).parsecmap(float)
_list_of     = lambda elems: _lbrace >> ps.many(elems) << _rbrace
_sep_list_of = lambda elems: _lbrace >> ps.sepBy(elems, _separator) << _rbrace

_param_value = _num_int | _list_of(_num_int)

@ps.generate
def _ldpc_key_value():
    key = yield _name
    val = yield _param_value
    return (key, val)

@ps.generate
def _ldpc_param():
    param_name = yield _name
    elems = yield _list_of(_ldpc_key_value)
    return (param_name, dict(elems))

@ps.generate
def _ldpc_param_table():
    params = yield ps.many(_ldpc_param)
    return dict(params)


# To round up the HWH parsing, let's define the name, C type, and parser
# combinator for each field we're interested in.


_config = [
    ('Standard'      , 'DRV_STANDARD'             , _num_int             ),
    ('Initialization', 'DRV_INITIALIZATION_PARAMS', _sep_list_of(_num_hex)),
]


_code_params = [
    ('ldpc', 'DRV_LDPC_PARAMS', _ldpc_param_table),
    # TODO Add Turbo code params
]


def _set_params(obj, params, config, *args):
    for c in config:
        setattr(obj, c[0], c[2].parse(params[c[1].format(*args)]))


def populate_params(obj, params):
    """Populates a given SdFec instance with parameters from an HWH file.
    
    Parameters include...
      + Basic IP config settings (XSdFec_Config struct)
      + LDPC parameter table (a dict of named XSdFecLdpcParameters)
    
    obj: An instance of SdFec
    params: Dict based on the HWH file snippet
    """
    obj._config = _ffi.new('XSdFec_Config*')
    obj._code_params = type('', (), {})
    _set_params(obj._config, params, _config)
    _set_params(obj._code_params, params, _code_params)


# Now we can build python structs from the HWH parameters, but we need to
# convert the types and field names to match the `XSdFecLdpcParameters`
# C struct. Be very careful about garbage collection here! If we do not store a
# reference to the inner C arrays, they will be garbage collected and make the
# LDPC codes incorrect! We solve this with a weakref dict - see https://cffi.readthedocs.io/en/latest/using.html#working-with-pointers-structures-and-arrays
# for details about the CFFI ownership model.

_c_array_weakkeydict = weakref.WeakKeyDictionary()

def _pack_ldpc_param(param_dict : dict) -> any:
    """Returns a cdata XSdFecLdpcParameters version of the given dict"""
    key_lookup = {
        'k': 'K',
        'n': 'N',
        'p': 'PSize',
        'nlayers': 'NLayers',
        'nqc': 'NQC',
        'nmqc': 'NMQC',
        'nm': 'NM',
        'norm_type': 'NormType',
        'no_packing': 'NoPacking',
        'special_qc': 'SpecialQC',
        'no_final_parity': 'NoFinalParity',
        'max_schedule': 'MaxSchedule',
        'sc_table': 'SCTable',
        'la_table': 'LATable',
        'qc_table': 'QCTable',
    }

    # Flush non-struct keys
    sub_dict = {key_lookup[key]: param_dict[key] for key in param_dict
                if key in key_lookup.keys()}
    
    # Pack tables as C arrays
    def to_c_array(lst):
        # Convert scalars to singleton lists
        if not isinstance(lst, list):
            lst = [lst]
        # Copy to C array
        c_arr = _ffi.new('u32[]', len(lst))
        for i, x in enumerate(lst):
            c_arr[i] = x
        return c_arr
    
    for table_key in filter(lambda k: k.endswith('Table'), sub_dict.keys()):
        sub_dict[table_key] = to_c_array(sub_dict[table_key])
    
    c_struct = _pack_value('XSdFecLdpcParameters', sub_dict)
    
    _c_array_weakkeydict[c_struct] = [sub_dict[table_key]
        for table_key in filter(lambda k: k.endswith('Table'), sub_dict.keys())
    ]
    
    return c_struct


# Let's load the compiled `.so` version of the driver and define some helper
# functions to marshall data to/from the driver. We want a couple of things
# here:
#   1. A wrapper to call C functions with C-style arguments
#   2. A pair of functions to wrap and unwrap python objects as C-style values


# Read in C function declarations
_THIS_DIR = os.path.dirname(__file__)
with open(os.path.join(_THIS_DIR, 'xsdfec_functions.c'), 'r') as f:
    _header_text = f.read()
_ffi = cffi.FFI()
_ffi.cdef(_header_text)
_lib = _ffi.dlopen(os.path.join(_THIS_DIR, 'libxsdfec.so'))


def _safe_wrapper(name: str, *args, check_return: bool=True, **kwargs) -> any:
    """Wrapper to call C functions, checking if they exist and their return status.
    
    name:         C function name
    check_return: Flag to treat return value as a status (non-zero is failure)
    return:       C function return value
    """
    with sys_pipes():
        if not hasattr(_lib, name):
            raise RuntimeError(f"Function {name} not in library")
        ret = getattr(_lib, name)(*args, **kwargs)
        if check_return and ret:
            raise RuntimeError(f"Function {name} call failed")
        return ret
    

def _pack_value(typename: str, value: any) -> any:
    """Pack a python object as a given C representation
    
    typename: Name of the C type (we can use type introspection
              to detect the Python type)
    value:    Python object to pack
    return:   C value
    """
    if isinstance(value, dict):
        c_value = _ffi.new(f"{typename}*")
        for k, v in value.items():
            setattr(c_value, k, v)
        value = c_value
    return value


def _unpack_value(typename: str, value: any) -> any:
    """Unpack given C data to a Python representation
    
    typename: Name of the C type (we can use type introspection
              to detect the Python type)
    value:    C value to unpack
    return:   Python object
    """
    if dir(value):
        return dict({k: getattr(value, k) for k in dir(value)})
    else:
        return value[0]


# With these helpers in place, we can start defining the SD FEC driver itself.
# 
# For initialisation, we parse parameters from the HWH file to populate an
# `XSdFec_Config` struct and pass this to the `XSdFecCfgInitialize` function.
# We also parse code parameter tables from the HWH file and keep them for
# later.
# 
# We add in wrapper functions for each of the four main API calls:
#    * `XSdFecSetTurboParams(InstancePtr, ParamsPtr)`
#    * `XSdFecAddLdpcParams(InstancePtr, CodeId, SCOffset, LAOffset, QCOffset, ParamsPtr)`
#    * `XSdFecShareTableSize(ParamsPtr, SCSizePtr, LASizePtr, QCSizePtr)`
#    * `XSdFecInterruptClassifier(InstancePtr)`


class SdFec(pynq.DefaultIP):
    """SD FEC driver"""
    bindto = ["xilinx.com:ip:sd_fec:1.1"]

    def __init__(self, description : dict):
        """Make an SD FEC instance as described by a HWH file snippet"""
        super().__init__(description)
        if 'parameters' in description:
            populate_params(self, description['parameters'])
        else:
            warnings.warn("Please use an hwh file with the SD-FEC driver"
                          " - the default configuration is being used")
            self._config = _lib.XSdFecLookupConfig(0)
            # TODO consider how we should set default LDPC and Turbo code params
        self._instance = _ffi.new("XSdFec*")
        self._config.BaseAddress = self.mmio.array.ctypes.data
        _lib.XSdFecCfgInitialize(self._instance, self._config)

    def _call_function(self, name: str, *args, **kwargs) -> any:
        """Helper function to call CFFI functions
        
        name: C function name (without "XSdFec" prefix)
        """
        return _safe_wrapper(f"XSdFec{name}", self._instance, *args, **kwargs)
    
    def available_ldpc_params(self) -> list:
        """List the available LDPC code names"""
        return list(self._code_params.ldpc.keys())
    
    def add_ldpc_params(self, code_id: int, sc_offset: int, la_offset: int, qc_offset: int, ldpc_param_name: str) -> None:
        """Add a named LDPC code at the given table offsets
        
        code_id:   Integer ID for new code
        sc_offset: Offset into SC table for new code
        la_offset: Offset into LA table for new code
        qc_offset: Offset into QC table for new code
        ldpc_param_name: Name of LDPC code to add (see available_ldpc_params() for valid options)
        """
        ldpc_c_param = _pack_ldpc_param(self._code_params.ldpc[ldpc_param_name])
        self._call_function('AddLdpcParams', code_id, sc_offset, la_offset, qc_offset,
                            ldpc_c_param)
    
    def set_turbo_params(self, turbo_params: dict) -> None:
        """Stub for setting Turbo code parameters"""
        # TODO
        pass
    
    def share_table_size(self, ldpc_param_name: str) -> tuple:
        """Helper function to get table sizes of a given LDPC code
        
        Useful for calculating table offsets when adding new LDPC codes.
        ldpc_param_name: Name of LDPC code (see available_ldpc_params() for valid options)
        return:          Dict with SC, LA, and QC table sizes
        """
        sc_size, la_size, qc_size = (_ffi.new('u32*'), _ffi.new('u32*'), _ffi.new('u32*'))
        _safe_wrapper('XSdFecShareTableSize', _pack_ldpc_param(self._code_params.ldpc[ldpc_param_name]),
                      sc_size, la_size, qc_size)
        return dict(sc_size = _unpack_value('u32*', sc_size),
                    la_size = _unpack_value('u32*', la_size),
                    qc_size = _unpack_value('u32*', qc_size))
    
    def interrupt_classifier(self) -> dict:
        """Get interrupt type information
        
        return: Dict with interrupt type info
        """
        return _unpack_value(
            'XSdFecInterruptClass',
            self._call_function('InterruptClassifier', check_return=False)
        )


# As well as the 4 main functions in the baremetal API, there are also getters
# and setters for individual registers. Let's expose them in a data-driven way.
# For each register we need to know 3 things:
# 
#   1. Register name
#   2. Register data type
#   3. Register access control (RW/RO/WO)
#   
# Let's just define a big list of all of this info for each register then write
# a generic function to attach these properties to the SD FEC driver.


from enum import Enum
class PropAccess(Enum):
    RW = 0
    RO = 1
    WO = 2

_core_props = [
    ("CORE_AXI_WR_PROTECT",           "u32", PropAccess.RW),
    ("CORE_CODE_WR_PROTECT",          "u32", PropAccess.RW),
    ("CORE_ACTIVE",                   "u32", PropAccess.RO),
    ("CORE_AXIS_WIDTH_DIN",           "u32", PropAccess.RW),
    ("CORE_AXIS_WIDTH_DIN_WORDS",     "u32", PropAccess.RW),
    ("CORE_AXIS_WIDTH_DOUT",          "u32", PropAccess.RW),
    ("CORE_AXIS_WIDTH_DOUT_WORDS",    "u32", PropAccess.RW),
    ("CORE_AXIS_WIDTH",               "u32", PropAccess.RW),
    ("CORE_AXIS_ENABLE_CTRL",         "u32", PropAccess.RW),
    ("CORE_AXIS_ENABLE_DIN",          "u32", PropAccess.RW),
    ("CORE_AXIS_ENABLE_DIN_WORDS",    "u32", PropAccess.RW),
    ("CORE_AXIS_ENABLE_STATUS",       "u32", PropAccess.RW),
    ("CORE_AXIS_ENABLE_DOUT",         "u32", PropAccess.RW),
    ("CORE_AXIS_ENABLE_DOUT_WORDS",   "u32", PropAccess.RW),
    ("CORE_AXIS_ENABLE",              "u32", PropAccess.RW),
    ("CORE_ORDER",                    "u32", PropAccess.RW),
    ("CORE_ISR",                      "u32", PropAccess.RW),
    ("CORE_IER",                      "u32", PropAccess.WO),
    ("CORE_IDR",                      "u32", PropAccess.WO),
    ("CORE_IMR",                      "u32", PropAccess.RO),
    ("CORE_ECC_ISR",                  "u32", PropAccess.RW),
    ("CORE_ECC_IER",                  "u32", PropAccess.WO),
    ("CORE_ECC_IDR",                  "u32", PropAccess.WO),
    ("CORE_ECC_IMR",                  "u32", PropAccess.RO),
    ("CORE_BYPASS",                   "u32", PropAccess.RW),
    ("CORE_VERSION",                  "u32", PropAccess.RO),   
    ("TURBO",                         "u32", PropAccess.RW),
    ("TURBO_ALG",                     "u32", PropAccess.RW),
    ("TURBO_SCALE_FACTOR",            "u32", PropAccess.RW),
    
]

       
class _PropertyDict(dict):
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


def _create_c_property(name: str, typename: str, access: PropAccess) -> property:
    """Create a getter and setter for a register description
    
    name:     Name of register
    typename: Name of C type that represents register value
    access:   Access control of the register (RW/RO/WO)
    return:   Python property for register
    """
    def _get(self):
        value =  _safe_wrapper(f"XSdFecGet_{name}", self._config.BaseAddress, check_return=False)
        if isinstance(value, dict):
            value = _PropertyDict(value)
            value.set_callback(lambda value: c_func(
                f"Set{name}", _pack_value(typename, value)))
        return value

    def _set(self, value):
        _safe_wrapper(f"XSdFecSet_{name}", self._config.BaseAddress, _pack_value(typename, value))

    if access == PropAccess.RO:
        return property(fget=_get)
    elif access == PropAccess.WO:
        return property(fset=_set)
    else:
        return property(_get, _set)


## Attach all registers as properties of SdFec class
for (prop_name, type_name, access) in _core_props:
    setattr(SdFec, prop_name, _create_c_property(prop_name, type_name, access))

    
## Define a list of all properties that get/set an entire array
_core_array_props = [
    ("LDPC_CODE_REG0",                       508/4, "u32", PropAccess.RW),
    ("LDPC_CODE_REG0_N",                     508/4, "u32", PropAccess.RW),
    ("LDPC_CODE_REG0_K",                     508/4, "u32", PropAccess.RW),
    ("LDPC_CODE_REG1",                       508/4, "u32", PropAccess.RW),
    ("LDPC_CODE_REG1_PSIZE",                 508/4, "u32", PropAccess.RW),
    ("LDPC_CODE_REG1_NO_PACKING",            508/4, "u32", PropAccess.RW),
    ("LDPC_CODE_REG1_NM",                    508/4, "u32", PropAccess.RW),
    ("LDPC_CODE_REG2",                       508/4, "u32", PropAccess.RW),
    ("LDPC_CODE_REG2_NLAYERS",               508/4, "u32", PropAccess.RW),
    ("LDPC_CODE_REG2_NMQC",                  508/4, "u32", PropAccess.RW),
    ("LDPC_CODE_REG2_NORM_TYPE",             508/4, "u32", PropAccess.RW),
    ("LDPC_CODE_REG2_SPECIAL_QC",            508/4, "u32", PropAccess.RW),
    ("LDPC_CODE_REG2_NO_FINAL_PARITY_CHECK", 508/4, "u32", PropAccess.RW),
    ("LDPC_CODE_REG2_MAX_SCHEDULE",          508/4, "u32", PropAccess.RW),
    ("LDPC_CODE_REG3",                       508/4, "u32", PropAccess.RW),
    ("LDPC_CODE_REG3_SC_OFF",                508/4, "u32", PropAccess.RW),
    ("LDPC_CODE_REG3_LA_OFF",                508/4, "u32", PropAccess.RW),
    ("LDPC_CODE_REG3_QC_OFF",                508/4, "u32", PropAccess.RW),
    ("LDPC_SC_TABLE",                        256/4, "u32", PropAccess.RW),
    ("LDPC_LA_TABLE",                       1024/4, "u32", PropAccess.RW),
    ("LDPC_QC_TABLE",                       8192/4, "u32", PropAccess.RW),
]


def _create_c_array_property(name: str, max_length: int, typename: str, access: PropAccess) -> property:
    """Create a getter and setter for an array description
    
    name:     Name of array
    length:   Number of elements in array
    typename: Name of C type that represents a single element
    access:   Access control of the register (RW/RO/WO)
    return:   Python property for array
    """
    def _get(self):
        word_offset = 0
        c_array = _ffi.new(typename+"[]", max_length)
        read_length =  _safe_wrapper(f"XSdFecRead_{name}",
            self._config.BaseAddress, word_offset, c_array, max_length,
            check_return=False)
        return [c_array[i] for i in range(read_length)]

    def _set(self, value):
        word_offset = 0
        c_array = _ffi.new(typename+"[]", len(value))
        for i, e in enumerate(value):
            c_array[i] = e
        _safe_wrapper(f"XSdFecWrite_{name}",
            self._config.BaseAddress, word_offset, c_array, len(value),
            check_return=False)

    if access == PropAccess.RO:
        return property(fget=_get)
    elif access == PropAccess.WO:
        return property(fset=_set)
    else:
        return property(_get, _set)


# Attach all registers as properties of SdFec class
for (prop_name, max_len, type_name, access) in _core_array_props:
    setattr(SdFec, prop_name, _create_c_array_property(prop_name+'_Words', int(max_len), type_name, access))
