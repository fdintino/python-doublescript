from __future__ import absolute_import

import ctypes
from ctypes import (
    POINTER, CFUNCTYPE, c_int, c_char_p, c_void_p, py_object, c_long, c_uint, c_ulong)
import sys

import seven

from .const import Py_ssize_t


def c_ptr(cls):
    ptr = POINTER(cls)

    def __getattr__(self, attr):
        if attr in dict(ptr._type_._fields_):
            if self:
                return getattr(self.contents, attr)
            else:
                return None
        else:
            return getattr(self.contents, attr)

    def __dir__(self):
        return sorted(set(
            self.__dict__.keys() +
            dir(self.__class__) +
            dict(ptr._type_._fields_).keys()))

    ptr.__getattr__ = __getattr__
    ptr.__dir__ = __dir__
    return ptr


c_int_p = c_ptr(c_int)
c_char_p_p = c_ptr(c_char_p)
c_void_p_p = c_ptr(c_void_p)
c_file_p = c_void_p
py_object_p = c_ptr(py_object)


Py_ssize_t_p = c_ptr(Py_ssize_t)
Py_hash_t = c_long if seven.PY2 else Py_ssize_t


class NullSafeStructure(ctypes.Structure):

    def __getattribute__(self, attr):
        try:
            return super(NullSafeStructure, self).__getattribute__(attr)
        except ValueError as e:
            if ("%s" % e).endswith('is NULL'):
                return None
            else:
                seven.reraise(*sys.exc_info())


class PyObject(NullSafeStructure):
    pass


PyObject_fields = [
    ('ob_refcnt', Py_ssize_t),
    ('ob_type', py_object),
]

if hasattr(sys, 'getobjects'):
    PyObject_fields = [
        ('_ob_next', c_ptr(PyObject)),
        ('_ob_prev', c_ptr(PyObject)),
    ] + PyObject_fields


PyObject._fields_ = PyObject_fields


class PyVarObject(PyObject):
    """ PyObject_VAR_HEAD """
    _fields_ = [('ob_size', Py_ssize_t)]


PyVarObject_p = c_ptr(PyVarObject)

unaryfunc = CFUNCTYPE(py_object, py_object)
binaryfunc = CFUNCTYPE(py_object, py_object, py_object)
ternaryfunc = CFUNCTYPE(py_object, py_object, py_object, py_object)
inquiry = CFUNCTYPE(c_int, py_object)
lenfunc = CFUNCTYPE(Py_ssize_t, py_object)
coercion = CFUNCTYPE(c_int, py_object_p, py_object_p)
ssizeargfunc = CFUNCTYPE(py_object, py_object, Py_ssize_t)
ssizessizeargfunc = CFUNCTYPE(py_object, py_object, Py_ssize_t, Py_ssize_t)
intobjargproc = CFUNCTYPE(c_int, py_object, c_int, py_object)
intintobjargproc = CFUNCTYPE(c_int, py_object, c_int, c_int, py_object)
ssizeobjargproc = CFUNCTYPE(c_int, py_object, Py_ssize_t, py_object)
ssizessizeobjargproc = CFUNCTYPE(c_int, py_object, Py_ssize_t, Py_ssize_t, py_object)
objobjargproc = CFUNCTYPE(c_int, py_object, py_object, py_object)
getreadbufferproc = CFUNCTYPE(c_int, py_object, c_int, c_void_p_p)
getwritebufferproc = CFUNCTYPE(c_int, py_object, c_int, c_void_p_p)
getsegcountproc = CFUNCTYPE(c_int, py_object, c_int_p)
getcharbufferproc = CFUNCTYPE(c_int, py_object, c_int, c_char_p_p)
readbufferproc = CFUNCTYPE(Py_ssize_t, py_object, Py_ssize_t, c_void_p_p)
writebufferproc = CFUNCTYPE(Py_ssize_t, py_object, Py_ssize_t, c_void_p_p)
segcountproc = CFUNCTYPE(Py_ssize_t, py_object, Py_ssize_t_p)
charbufferproc = CFUNCTYPE(Py_ssize_t, py_object, Py_ssize_t, c_char_p_p)


class bufferinfo(NullSafeStructure):
    _fields_ = [
        ('buf', c_void_p),
        ('obj', py_object),
        ('len', Py_ssize_t),
        ('itemsize', Py_ssize_t),
        ('readonly', c_int),
        ('ndim', c_int),
        ('format', c_char_p),
        ('shape', Py_ssize_t_p),
        ('strides', Py_ssize_t_p),
        ('suboffsets', Py_ssize_t_p),
        ('smalltable', Py_ssize_t * 2),
        ('internal', c_void_p),
    ]


bufferinfo_p = c_ptr(bufferinfo)
Py_buffer = bufferinfo
Py_buffer_p = c_ptr(Py_buffer)
getbufferproc = CFUNCTYPE(c_int, py_object, Py_buffer_p, c_int)
releasebufferproc = CFUNCTYPE(None, py_object, Py_buffer_p)
objobjproc = CFUNCTYPE(c_int, py_object, py_object)
visitproc = CFUNCTYPE(c_int, py_object, c_void_p)
traverseproc = CFUNCTYPE(c_int, py_object, visitproc, c_void_p)


class PyNumberMethods(NullSafeStructure):
    _fields_ = [
        ('nb_add', binaryfunc),
        ('nb_subtract', binaryfunc),
        ('nb_multiply', binaryfunc),
    ] + ([('nb_divide', binaryfunc)] if seven.PY2 else []) + [
        ('nb_remainder', binaryfunc),
        ('nb_divmod', binaryfunc),
        ('nb_power', ternaryfunc),
        ('nb_negative', unaryfunc),
        ('nb_positive', unaryfunc),
        ('nb_absolute', unaryfunc),
        ('nb_bool', inquiry),  # nb_nonzero in python 2
        ('nb_invert', unaryfunc),
        ('nb_lshift', binaryfunc),
        ('nb_rshift', binaryfunc),
        ('nb_and', binaryfunc),
        ('nb_xor', binaryfunc),
        ('nb_or', binaryfunc),
    ] + ([('nb_coerce', coercion)] if seven.PY2 else []) + [
        ('nb_int', unaryfunc),
        ('nb_long', unaryfunc),  # nb_reserved in python 3
        ('nb_float', unaryfunc),
    ] + ([] if seven.PY3 else [
        ('nb_oct', unaryfunc),
        ('nb_hex', unaryfunc),
    ]) + [
        ('nb_inplace_add', binaryfunc),
        ('nb_inplace_subtract', binaryfunc),
        ('nb_inplace_multiply', binaryfunc),
    ] + ([('nb_inplace_divide', binaryfunc)] if seven.PY2 else []) + [
        ('nb_inplace_remainder', binaryfunc),
        ('nb_inplace_power', ternaryfunc),
        ('nb_inplace_lshift', binaryfunc),
        ('nb_inplace_rshift', binaryfunc),
        ('nb_inplace_and', binaryfunc),
        ('nb_inplace_xor', binaryfunc),
        ('nb_inplace_or', binaryfunc),
        ('nb_floor_divide', binaryfunc),
        ('nb_true_divide', binaryfunc),
        ('nb_inplace_floor_divide', binaryfunc),
        ('nb_inplace_true_divide', binaryfunc),
        ('nb_index', unaryfunc),
    ] + ([] if seven.PY2 else [
        ('nb_matrix_multiply', binaryfunc),
        ('nb_inplace_matrix_multiple', binaryfunc),
    ])


PyNumberMethods_p = c_ptr(PyNumberMethods)


class PySequenceMethods(NullSafeStructure):
    """
    lenfunc sq_length;
     binaryfunc sq_concat;
     ssizeargfunc sq_repeat;
     ssizeargfunc sq_item;
     ssizessizeargfunc sq_slice;
     ssizeobjargproc sq_ass_item;
     ssizessizeobjargproc sq_ass_slice;
     objobjproc sq_contains;
     binaryfunc sq_inplace_concat;
     ssizeargfunc sq_inplace_repeat;
    """
    _fields_ = [
        ('sq_length', lenfunc),
        ('sq_concat', binaryfunc),
        ('sq_repeat', ssizeargfunc),
        ('sq_item', ssizeargfunc),
        ('sq_slice', ssizessizeargfunc),  # was_sq_slice in python 3
        ('sq_ass_item', ssizeobjargproc),
        ('sq_ass_slice', ssizessizeobjargproc),  # was_sq_ass_slice in python 3
        ('sq_contains', objobjproc),
        ('sq_inplace_concat', binaryfunc),
        ('sq_inplace_repeat', ssizeargfunc),
    ]


PySequenceMethods_p = c_ptr(PySequenceMethods)


class PyMappingMethods(NullSafeStructure):
    _fields_ = [
        ('mp_length', lenfunc),
        ('mp_subscript', binaryfunc),
        ('mp_ass_subscript', objobjargproc),
    ]


PyMappingMethods_p = c_ptr(PyMappingMethods)


class PyAsyncMethods(NullSafeStructure):
    _fields_ = [
        ('am_await', unaryfunc),
        ('am_aiter', unaryfunc),
        ('am_anext', unaryfunc),
    ]


PyAsyncMethods_p = c_ptr(PyAsyncMethods)


class PyBufferProcs(NullSafeStructure):
    _fields_ = [
        ('bf_getreadbuffer', readbufferproc),
        ('bf_getwritebuffer', writebufferproc),
        ('bf_getsegcount', segcountproc),
        ('bf_getcharbuffer', charbufferproc),
        ('bf_getbuffer', getbufferproc),
        ('bf_releasebuffer', releasebufferproc),
    ]


PyBufferProcs_p = c_ptr(PyBufferProcs)
freefunc = CFUNCTYPE(None, c_void_p)
destructor = CFUNCTYPE(None, py_object)
printfunc = CFUNCTYPE(c_int, py_object, c_file_p, c_int)
getattrfunc = CFUNCTYPE(py_object, py_object, c_char_p)
getattrofunc = CFUNCTYPE(py_object, py_object, py_object)
setattrfunc = CFUNCTYPE(c_int, py_object, c_char_p, py_object)
setattrofunc = CFUNCTYPE(c_int, py_object, py_object, py_object)
cmpfunc = CFUNCTYPE(c_int, py_object, py_object)
reprfunc = CFUNCTYPE(py_object, py_object)
hashfunc = CFUNCTYPE(Py_hash_t, py_object)
richcmpfunc = CFUNCTYPE(py_object, py_object, py_object, c_int)
getiterfunc = CFUNCTYPE(py_object, py_object)
iternextfunc = CFUNCTYPE(py_object, py_object)
descrgetfunc = CFUNCTYPE(py_object, py_object, py_object, py_object)
descrsetfunc = CFUNCTYPE(c_int, py_object, py_object, py_object)
initproc = CFUNCTYPE(c_int, py_object, py_object, py_object)


class PyTypeObject(NullSafeStructure):
    pass


PyTypeObject_p = c_ptr(PyTypeObject)

newfunc = CFUNCTYPE(py_object, PyTypeObject_p, py_object, py_object)
allocfunc = CFUNCTYPE(py_object, PyTypeObject_p, Py_ssize_t)

PyTypeObject._fields_ = [
    ('ob_refcnt', Py_ssize_t),
    ('ob_type', py_object),
] + PyObject_fields[2:] + [
    ('ob_size', Py_ssize_t),
    ('tp_name', c_char_p),
    ('tp_basicsize', Py_ssize_t),
    ('tp_itemsize', Py_ssize_t),
    ('tp_dealloc', destructor),
    ('tp_print', printfunc),
    ('tp_getattr', getattrfunc),
    ('tp_setattr', setattrfunc),
    # tp_compare is tp_as_async in python 3.5, tp_reserved in earlier python 3
    ('tp_compare', ctypes.c_void_p),
    ('tp_repr', reprfunc),
    ('tp_as_number', PyNumberMethods_p),
    ('tp_as_sequence', PySequenceMethods_p),
    ('tp_as_mapping', PyMappingMethods_p),
    ('tp_hash', hashfunc),
    ('tp_call', ternaryfunc),
    ('tp_str', reprfunc),
    ('tp_getattro', getattrofunc),
    ('tp_setattro', setattrofunc),
    ('tp_as_buffer', PyBufferProcs_p),
    ('tp_flags', c_long if seven.PY2 else c_ulong),
    ('tp_doc', c_char_p),
    ('tp_traverse', traverseproc),
    ('tp_clear', inquiry),
    ('tp_richcompare', richcmpfunc),
    ('tp_weaklistoffset', Py_ssize_t),
    ('tp_iter', getiterfunc),
    ('tp_iternext', iternextfunc),
    ('tp_methods', c_void_p),
    ('tp_members', c_void_p),
    ('tp_getset', c_void_p),
    ('tp_base', py_object),
    ('tp_dict', py_object),
    ('tp_descr_get', descrgetfunc),
    ('tp_descr_set', descrsetfunc),
    ('tp_dictoffset', Py_ssize_t),
    ('tp_init', initproc),
    ('tp_alloc', allocfunc),
    ('tp_new', newfunc),
    ('tp_free', freefunc),
    ('tp_is_gc', inquiry),
    ('tp_bases', py_object),
    ('tp_mro', py_object),
    ('tp_cache', py_object),
    ('tp_subclasses', py_object),
    ('tp_weaklist', py_object),
    ('tp_del', destructor),
    ('tp_version_tag', c_uint),
]


class PyClassObject(NullSafeStructure):
    _fields_ = [
        ('ob_refcnt', Py_ssize_t),
        ('ob_type', py_object),
        ('cl_bases', py_object),
        ('cl_dict', py_object),
        ('cl_name', py_object),
        ('cl_getattr', py_object),
        ('cl_setattr', py_object),
        ('cl_delattr', py_object),
        ('cl_weakreflist', py_object),
    ]


class PyInstanceObject(NullSafeStructure):
    _fields_ = [
        ('ob_refcnt', Py_ssize_t),
        ('ob_type', py_object),
        ('in_class', py_object),
        ('in_dict', py_object),
        ('in_weakreflist', py_object),
    ]


class PyFunctionObject(NullSafeStructure):
    _fields_ = [
        ('ob_refcnt', Py_ssize_t),
        ('ob_type', py_object),
        ('func_code', py_object),
        ('func_defaults', py_object),
        ('func_closure', py_object),
        ('func_doc', py_object),
        ('func_name', py_object),
        ('func_dict', py_object),
        ('func_weakreflist', py_object),
        ('func_module', py_object),
    ]


wrapperfunc = CFUNCTYPE(py_object, py_object, py_object, c_void_p)


class PyDescrObject(NullSafeStructure):
    _fields_ = PyObject_fields + [
        ('d_type', py_object),
        ('d_name', py_object),
    ] + ([('d_qualname', py_object)] if seven.PY3 else [])


class wrapperbase(NullSafeStructure):
    _fields_ = [
        ('name', c_char_p),
        ('offset', c_int),
        ('function', c_void_p),
        ('wrapper', wrapperfunc),
        ('doc', c_char_p),
        ('flags', c_int),
        ('name_strobj', py_object),
    ]


class PyWrapperDescrObject(NullSafeStructure):
    _fields_ = PyDescrObject._fields_ + [
        ('d_base', c_ptr(wrapperbase)),
        ('d_wrapped', c_void_p),
    ]


class CDataObject(NullSafeStructure):
    pass


CDataObject._fields_ = PyObject_fields + [
    ('b_ptr', Py_ssize_t),
    ('b_needsfree', c_int),
    ('b_base', c_ptr(CDataObject)),
    ('b_size', Py_ssize_t),
    ('b_length', Py_ssize_t),
    ('b_index', Py_ssize_t),
    ('b_objects', py_object),
]


class DictProxy(PyObject):
    _fields_ = [('dict', ctypes.POINTER(PyObject))]


def c_typeobj(t):
    return PyTypeObject.from_address(id(t))
