import ctypes
from ctypes import c_void_p, c_size_t, c_int, py_object, pythonapi, CFUNCTYPE, c_ubyte
import struct

from .utils import cdata_ptr
from .refs import Py_INCREF

import resource

libc = ctypes.CDLL(ctypes.util.find_library('libc'))


libc.mprotect.argtypes = [c_void_p, c_size_t, c_int]
libc.mprotect.restype = c_int


def pycode_optimize(args):
    code = args[0]
    Py_INCREF(code)
    return id(code)


Override_PyCode_Optimize = CFUNCTYPE(c_void_p, *[py_object * 4])(pycode_optimize)


def override_function(cfunc, new_cfunc):
    old_cfunc_ptr = cdata_ptr(cfunc)
    new_cfunc_ptr = cdata_ptr(new_cfunc)
    page_size = resource.getpagesize()
    page_boundary = int((old_cfunc_ptr // page_size) * page_size)
    if libc.mprotect(page_boundary, page_size, 7) == -1:
        raise Exception("mprotect failed")
    offset = new_cfunc_ptr - old_cfunc_ptr
    opcodes = map(ord, '\xe9%s' % struct.pack('<l', offset - 5))
    old_cfunc_mem = (c_ubyte * 5).from_address(old_cfunc_ptr)
    old_cfunc_mem[0:5] = opcodes


def override_pycode_optimize():
    override_function(pythonapi.PyCode_Optimize, Override_PyCode_Optimize)
