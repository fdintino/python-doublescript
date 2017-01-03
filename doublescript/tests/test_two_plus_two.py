from __future__ import print_function

import unittest

from doublescript import two_plus_two_equals


class TwoPlusTwoTestCase(unittest.TestCase):

    def test_twoplustwo_eval(self):
        with two_plus_two_equals(5):
            self.assertEqual(eval("2 + 2"), 5)

    # Fails if PyCode_Optimize isn't overridden, because that function
    # replaces inline binary operations with their evaluated result when
    # generating the python opcodes.
    #
    # Needless to say, if pyc files are created without this preloaded shared
    # library, they will have the "2 + 2" collapsed to "4" in the opcodes.
    def test_twoplustwo_inline(self):
        with two_plus_two_equals(5):
            self.assertEqual(2 + 2, 5)
