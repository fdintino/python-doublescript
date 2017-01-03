import ctypes
from ctypes import c_void_p, c_size_t, c_int, py_object, pythonapi, CFUNCTYPE, c_ubyte
import errno
import os
import platform
import resource
import struct
import warnings

import seven

from .utils import cdata_ptr
from .refs import Py_INCREF


PAGE_SIZE = resource.getpagesize()


PROT_NONE = 0   # The memory cannot be accessed at all
PROT_READ = 1   # The memory can be read
PROT_WRITE = 2  # The momory can be modified
PROT_EXEC = 4   # The memory can be executed


# TODO: Use VirtualProtect on windows
def mprotect(addr, size, flags):
    if addr % PAGE_SIZE != 0:
        raise Exception("mprotect address must be aligned to a page boundary")
    if not isinstance(addr, seven.integer_types):
        raise ValueError("addr must be an integer type")
    if not isinstance(size, seven.integer_types):
        raise ValueError("size must be an integer type")
    if not isinstance(flags, seven.integer_types):
        raise ValueError("flags must be an integer type")
    if flags & ~PROT_READ & ~PROT_WRITE & ~PROT_EXEC:
        raise ValueError(
            "flags must be a bitmask of PROT_NONE(%d), PROT_READ (%d), "
            "PROT_WRITE (%d), and/or PROT_EXEC (%d)" % (
                PROT_NONE, PROT_READ, PROT_WRITE, PROT_EXEC))
    libc = ctypes.CDLL(ctypes.util.find_library('libc'), use_errno=True)
    libc.mprotect.argtypes = [c_void_p, c_size_t, c_int]
    libc.mprotect.restype = c_int
    ret = libc.mprotect(addr, size, flags)
    if ret == -1:
        e = ctypes.get_errno()
        raise OSError(e, errno.errorcodes[e], os.strerror(e))


def pycode_optimize(code, consts, name, lineno_obj):
    Py_INCREF(code)
    return id(code)


quaternaryfunc = CFUNCTYPE(
    c_void_p, py_object, py_object, py_object, py_object)


Override_PyCode_Optimize = quaternaryfunc(pycode_optimize)


def is_x86():
    return platform.machine() in ('i386', 'i486', 'i586', 'i686', 'x86', 'x86_64')


def is_windows():
    return platform.system() == 'Windows'


class UnsupportedPlatformException(Exception):
    pass


def force_ord(char):
    """
    In python 3, casting bytes to a list returns a list of ints rather than
    a list of bytes, as python 2 does (with str)
    """
    return char if isinstance(char, int) else ord(char)


def override_cfunc(cfunc, new_cfunc):
    if not is_x86():
        raise UnsupportedPlatformException(
            "override_cfunc() only works on x86 architectures")
    if is_windows():
        raise UnsupportedPlatformException(
            "override_cfunc() does not work on windows")
    old_cfunc_ptr = cdata_ptr(cfunc)
    new_cfunc_ptr = cdata_ptr(new_cfunc)
    page_boundary = int((old_cfunc_ptr // PAGE_SIZE) * PAGE_SIZE)
    memlen = PAGE_SIZE
    # In the unlikely event that the first five bytes of the function occur
    # across a page boundary, we need to call mprotect on two pages
    if page_boundary + PAGE_SIZE - old_cfunc_ptr < 5:
        memlen *= 2
    mprotect(page_boundary, memlen, PROT_READ | PROT_WRITE | PROT_EXEC)
    offset = new_cfunc_ptr - old_cfunc_ptr
    JMP = b'\xe9'
    opcodes = list(map(force_ord, JMP + struct.pack('<l', offset - 5)))
    old_cfunc_mem = (c_ubyte * 5).from_address(old_cfunc_ptr)
    old_cfunc_mem[0:5] = opcodes


def disable_pycode_optimize():
    try:
        override_cfunc(pythonapi.PyCode_Optimize, Override_PyCode_Optimize)
    except UnsupportedPlatformException as e:
        warnings.warn("%s" % e)
