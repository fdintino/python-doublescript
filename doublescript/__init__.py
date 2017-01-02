import pkg_resources
import sys

import six
import contextlib
import threading

# Alias the ``six`` module to ``seven``, for obvious reasons
sys.modules['seven'] = six

from doublescript.internals.const import Py_TPFLAGS  # noqa
from doublescript.internals.utils import clone_type  # noqa
from doublescript.internals.structs import PyTypeObject  # noqa
from doublescript.internals.typeobject import override_type, type_set_bases  # noqa


try:
    __version__ = pkg_resources.get_distribution('python-doublescript').version
except pkg_resources.DistributionNotFound:
    __version__ = None

thread_data = threading.local()


def __add__(self, other):
    if self == other == 2:
        return thread_data.__dict__.setdefault('two_plus_two', 4)
    else:
        with override_type(self, int):
            with override_type(other, int):
                return int.__add__(self, other)


def set_two_plus_two(new_sum):
    thread_data.two_plus_two = new_sum


int2 = clone_type(int, bases=(int,), __add__=__add__)
type_set_bases(int2, (int,))
PyInt2_Type = PyTypeObject.from_address(id(int2))
PyInt2_Type.tp_name = b'int2'
PyInt2_Type.tp_flags &= ~Py_TPFLAGS.INT_SUBCLASS


@contextlib.contextmanager
def change_two_plus_two(new_sum):
    old_val = thread_data.__dict__.setdefault('two_plus_two', 4)
    thread_data.two_plus_two = new_sum
    with override_type(2, int2):
        yield
    thread_data.two_plus_two = old_val
