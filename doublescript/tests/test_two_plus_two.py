from __future__ import print_function

import unittest

from doublescript import change_two_plus_two
from doublescript.internals.typeobject import set_type


class TwoPlusTwoTestCase(unittest.TestCase):

    def test_twoplustwo_eval(self):
        with change_two_plus_two(5):
            self.assertEqual(eval("2 + 2"), 5)

    # Fails if PyCode_Optimize isn't overridden, because that function
    # replaces inline binary operations with their evaluated result when
    # generating the python opcodes.
    #
    # It might be possible to override this function using only ctypes,
    # but the easiest way to override it is to load a platform-specific
    # shared library using either LD_PRELOAD with an interposed function
    # on linux, or DYLD_INSERT_LIBRARIES with mach_override on OS X.
    #
    # Needless to say, if pyc files are created without this preloaded shared
    # library, they will have the "2 + 2" collapsed to "4" in the opcodes.
    @unittest.expectedFailure
    def test_twoplustwo_inline(self):
        with change_two_plus_two(5):
            self.assertEqual(2 + 2, 5)
