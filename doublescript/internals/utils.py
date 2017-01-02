import ctypes
from ctypes import py_object, POINTER, c_void_p

from .api import pythonapi
from .const import Py_TPFLAGS
from .refs import Py_INCREF
from .structs import DictProxy, CDataObject, PyTypeObject
from .typeobject import is_heap_type, type_set_bases


DictProxyType = type(type.__dict__)

CDataType = ctypes._Pointer.__bases__[0]


def get_pointer(cdata):
    return ctypes.cast(ctypes.byref(cdata), POINTER(c_void_p)).contents.value


def struct_to_py_object(d):
    if not isinstance(d, CDataType):
        raise TypeError("Must be a ctypes._CData instance")
    if isinstance(d, ctypes._Pointer):
        cdata = d.contents
    else:
        cdata = d
    cdata_obj = CDataObject.from_address(id(cdata))
    cdata_obj.b_needsfree = 0
    ns = {}
    pythonapi.PyDict_SetItem(py_object(ns), py_object(None), ctypes.pointer(cdata))
    return ns[None]


def mutable_class_dict(cls):
    """Returns a mutable instance of ``cls.__dict__``"""
    d = getattr(cls, '__dict__', None)
    if d is None:
        raise TypeError('given class does not have a dictionary')
    if not isinstance(d, DictProxyType):
        return d

    dp = DictProxy.from_address(id(d))
    return struct_to_py_object(dp.dict)


def clone_type(cls, name=None, bases=None, tp_fields=None, **kwargs):
    if not isinstance(cls, type):
        raise TypeError("clone_type cls must be a type")
    if is_heap_type(cls):
        metaclass = type(cls)
        d = dict(cls.__dict__).update(kwargs)
        return metaclass(name or cls.__name__, bases or cls.__bases__, d)
    c_type = PyTypeObject.from_address(id(cls))
    field_vals = {}
    tp_fields = tp_fields or {}
    if name:
        Py_INCREF(name)
        tp_fields.setdefault('tp_name', name)
    for i, (field_name, field_type) in enumerate(PyTypeObject._fields_):
        if field_name in (
                'tp_dict', 'tp_bases', 'tp_mro', 'tp_cache',
                'tp_subclasses', 'tp_weaklist', 'tp_version_tag',
                'ob_refcnt', '_ob_next', '_ob_prev'):
            continue
        val = getattr(c_type, field_name)
        if val is None:
            continue
        if field_name == 'tp_flags':
            val &= ~Py_TPFLAGS.VALID_VERSION_TAG & ~Py_TPFLAGS.READY & ~Py_TPFLAGS.READYING
            if val == 0:
                continue
        field_vals[field_name] = val

    field_vals.update(tp_fields)
    field_vals['ob_refcnt'] = 1
    new_c_type = PyTypeObject(**field_vals)
    err = pythonapi.PyType_Ready(ctypes.pointer(new_c_type))
    if err < 0:
        raise Exception("Failed to ready clone of %s" % cls.__name__)
    new_type = struct_to_py_object(new_c_type)
    new_clsdict = mutable_class_dict(new_type)
    new_clsdict.update(kwargs)
    if bases:
        type_set_bases(new_type, bases)
    return new_type


def addressof(o):
    """
    Returns ctypes.addressof if the object is an instance of ctypes._CData,
    otherwise returns id(o).

    This makes it so that this function returns the same value for a ctypes
    Structure representation of python object as the python object itself.
    """
    if isinstance(o, CDataType):
        return ctypes.addressof(o)
    else:
        return id(o)
