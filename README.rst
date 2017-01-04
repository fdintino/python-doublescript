python-doublescript
===================

python-doublescript is a package that allows runtime manipulation of the
evaluated value of “2 + 2” (generally to cause the result to equal “5”).
The name of the package and the specific focus on
`“2 + 2 = 5” <https://en.wikipedia.org/wiki/2_%2B_2_%3D_5>`_ comes from the
novel *1984* by George Orwell, but the motivation is to explore CPython
internals and how one would go about monkey-patching those internals at
runtime using ctypes.

Usage
-----

.. code-block:: python

    from doublescript import two_plus_two_equals

    with two_plus_two_equals(5):
        print(eval("2 + 2"))  # prints "5"

Or, if you’re feeling adventurous (currently only works on x86 architectures
running some flavor of Linux/Unix/BSD, including OS X)::

    export DOUBLEPLUSNOPYTHONOPT=1

    python

    In [1]: with two_plus_two_equals(5):
       ...:     print(2 + 2)
       ...:
    5

Caveats
-------

This implementation is CPython-specific, so it won’t work with other
python interpreters (e.g., PyPy). Another thing to consider is that python
folds binary operations when generating opcode as an optimization. What this
means in practice is that an inline ``2 + 2`` (as opposed to ``eval("2 + 2")``)
will simply become ``4`` in the opcodes. This python behavior can be disabled
by setting the environment variable ``DOUBLEPLUSNOPYTHONOPT`` before running
your scripts. This applies equally to .pyc files: if the pyc files were
generated with the normal python opcode optimizations, this library will have
no effect on inline ``2 + 2`` expressions, since they will have already been
turned into ``4``. At present, disabling opcode optimizations only works in x86
architectures, and it does not currently work on windows.

License
-------

Copyright (©) The Ministry of Truth, 1984. Licensed under the `Simplified BSD
License <http://opensource.org/licenses/BSD-2-Clause>`_. View the
``LICENSE`` file under the root directory for complete license and
copyright information.
