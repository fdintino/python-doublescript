import ctypes
import ctypes.util
from ctypes import (
    c_void_p, c_size_t, c_int, py_object, pythonapi, CFUNCTYPE, c_ubyte,
    c_long, c_ulong, c_ulonglong, POINTER)
import errno
import os
import platform
import struct
import warnings

import seven

from .utils import cdata_ptr
from .refs import Py_INCREF

try:
    import resource
except ImportError:
    PAGE_SIZE = None  # windows
else:
    PAGE_SIZE = resource.getpagesize()


IS_X86 = (platform.machine() in ('i386', 'i486', 'i586', 'i686', 'x86', 'x86_64'))
IS_WINDOWS = (platform.system() == 'Windows')
IS_64BIT = ctypes.sizeof(c_void_p) == ctypes.sizeof(c_ulonglong)

# <sys/mman.h> constants
PROT_NONE = 0   # The memory cannot be accessed at all
PROT_READ = 1   # The memory can be read
PROT_WRITE = 2  # The momory can be modified
PROT_EXEC = 4   # The memory can be executed

# Microsoft, what's the point of using bitmasks if you can't OR the values?
PAGE_NOACCESS = 0x01
PAGE_READONLY = 0x02
PAGE_READWRITE = 0x04
PAGE_WRITECOPY = 0x08
PAGE_EXECUTE = 0x10
PAGE_EXECUTE_READ = 0x20
PAGE_EXECUTE_READWRITE = 0x40

MS_PAGE_CONSTANTS = {
    PROT_NONE: PAGE_NOACCESS,
    PROT_READ: PAGE_READONLY,
    PROT_WRITE: PAGE_READWRITE,
    (PROT_WRITE | PROT_READ): PAGE_READWRITE,
    PROT_EXEC: PAGE_EXECUTE,
    (PROT_EXEC | PROT_READ): PAGE_EXECUTE_READ,
    (PROT_EXEC | PROT_WRITE): PAGE_EXECUTE_READWRITE,
    (PROT_EXEC | PROT_WRITE | PROT_READ): PAGE_EXECUTE_READWRITE,
}

# windows datatypes
BOOL = c_long
DWORD = c_ulong
SIZE_T = c_ulonglong if IS_64BIT else DWORD
LPVOID = c_void_p
PDWORD = POINTER(DWORD)


def mprotect_winapi(addr, size, flags):
    kernel32 = ctypes.windll.kernel32
    VirtualProtect = kernel32.VirtualProtect
    VirtualProtect.argtypes = [LPVOID, SIZE_T, DWORD, PDWORD]
    VirtualProtect.restype = BOOL
    old_prot = DWORD()
    prot = MS_PAGE_CONSTANTS[flags]
    ret = VirtualProtect(addr, size, prot, ctypes.byref(old_prot))
    if not ret:
        raise ctypes.WinError()


def mprotect_libc(addr, size, flags):
    libc = ctypes.CDLL(ctypes.util.find_library('libc'), use_errno=True)
    libc.mprotect.argtypes = [c_void_p, c_size_t, c_int]
    libc.mprotect.restype = c_int
    addr_align = addr & ~(PAGE_SIZE - 1)
    mem_end = (addr + size) & ~(PAGE_SIZE - 1)
    if (addr + size) > mem_end:
        mem_end += PAGE_SIZE
    memlen = mem_end - addr_align
    ret = libc.mprotect(addr_align, memlen, flags)
    if ret == -1:
        e = ctypes.get_errno()
        raise OSError(e, errno.errorcodes[e], os.strerror(e))


def mprotect(addr, size, flags):
    """
    A cross-platform mprotect function (calls VirtualProtect on windows,
    mprotect otherwise).

    For mprotect_libc, addr does not have to be aligned to page boundaries;
    this implementation will ensure that an aligned address gets passed.
    """
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
    if IS_WINDOWS:
        mprotect_winapi(addr, size, flags)
    else:
        mprotect_libc(addr, size, flags)


def noop_pycode_optimize(code, consts, name, lineno_obj):
    """
    A function intended to replace PyCode_Optimize. Whereas PyCode_Optimize
    takes ``code`` (python bytecode) and returns peephole-optimized bytecode,
    this function effectively disables the peephole optimizer by simply
    returning the original bytecode after incrementing its reference count.
    """
    Py_INCREF(code)
    # ctypes doesn't allow returning pointers to python objects, so we simply
    # return the address of the PyObject
    return id(code)


quaternaryfunc = CFUNCTYPE(
    c_void_p, py_object, py_object, py_object, py_object)


NoOp_PyCode_Optimize = quaternaryfunc(noop_pycode_optimize)


class UnsupportedPlatformException(Exception):
    pass


def force_ord(char):
    """
    In python 3, casting bytes to a list returns a list of ints rather than
    a list of bytes, as python 2 does (with str)
    """
    return char if isinstance(char, int) else ord(char)


def override_cfunc(cfunc, new_cfunc):
    """
    Overrides a CFUNCTION by inserting a JMP instruction at the function's
    address in memory.

    If the new cfunction doesn't have the same prototype as the old one,
    this will almost certainly cause a segfault.
    """
    if not IS_X86:
        raise UnsupportedPlatformException(
            "override_cfunc() only works on x86 architectures")
    old_cfunc_ptr = cdata_ptr(cfunc)
    new_cfunc_ptr = cdata_ptr(new_cfunc)
    mprotect(old_cfunc_ptr, 5, PROT_READ | PROT_WRITE | PROT_EXEC)
    offset = new_cfunc_ptr - old_cfunc_ptr
    JMP = b'\xe9'
    opcodes = list(map(force_ord, JMP + struct.pack('<l', offset - 5)))
    old_cfunc_mem = (c_ubyte * 5).from_address(old_cfunc_ptr)
    old_cfunc_mem[0:5] = opcodes


def disable_peephole_optimizer():
    try:
        override_cfunc(pythonapi.PyCode_Optimize, NoOp_PyCode_Optimize)
    except UnsupportedPlatformException as e:
        warnings.warn("%s" % e)
