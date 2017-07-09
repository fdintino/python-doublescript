import os
import unittest
import sys

from doublescript.asm_hooks import disable_peephole_optimizer


sys.dont_write_bytecode = True
disable_peephole_optimizer()

current_dir = os.path.abspath(os.path.dirname(__file__))
test_dir = os.path.join(current_dir, 'doublescript', 'tests')


if __name__ == '__main__':
    loader = unittest.TestLoader()
    suite = loader.discover(test_dir, top_level_dir=current_dir)
    results = unittest.TextTestRunner().run(suite)
    if results.failures or results.errors:
        sys.exit(1)
