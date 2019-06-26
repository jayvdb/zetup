"""
Simplify command line argument definitions for ``console_scripts``.

Every according script entry function is termed a :class:`zetup.program` in
this context
"""

from __future__ import absolute_import

import sys
from argparse import ArgumentParser

import zetup

from .object import object

__all__ = ('program', 'with_arguments')


class program(ArgumentParser, object):
    """
    Decorator for entry functions of ``console_scripts``.

    Simplifies argument handling a lot by integration with
    :class:`zetup.with_argument` instead of directly using multiple calls to
    ``argparse.ArgumentParser.add_argument``:

    >>> import zetup
    >>> from zetup import program, with_arguments

    >>> @program(
    ...     with_arguments
    ...     ('--version', action='store_true')
    ...     ('--class')
    ... )
    ... def explain(args):
    ...     if args.version:
    ...         print(zetup.__version__)
    ...         sys.exit(0)
    ...
    ...     from importlib import import_module
    ...     modname, clsname = getattr(args, 'class').rsplit('.', 1)
    ...     mod = import_module(modname)
    ...     print(help(getattr(mod, clsname)))
    ...     sys.exit(0)

    As a (kind of) real life example, the above would of course end the Python
    process. That's why ``SystemExit`` is catched here for demonstration
    purposes, and expicit arg lists are given instead of implicitly using
    ``sys.argv``:

    >>> try:
    ...     explain(['--version'])
    ... except SystemExit as exc:
    ...     assert exc.code == 0
    {zetup_version}

    >>> try:
    ...     explain(['--class', 'zetup.program'])
    ... except SystemExit as exc:
    ...     assert exc.code == 0
    Help on class program in module zetup.program:
    ...
    """

    # the variables in curly braces in the doc string above are substituted
    # below the program class definition

    def __init__(self, arguments, **kwargs):
        """
        Prepare the decorator with a :class:`zetup.with_arguments` object.

        All `kwargs` are delegated to the ``ArgumentParser`` base constructor
        """
        ArgumentParser.__init__(self, **kwargs)
        for args, kwargs in arguments:
            self.add_argument(*args, **kwargs)

    def __call__(self, func):
        """
        Wrap `func` with an automatic :meth:`zetup.program.parse_args` step.

        So that `func` can directly work with the parser result object
        """
        def caller(argv=None):
            """
            Wrap function with auto-parsing of `argv` or default ``sys.argv``.

            Then pass the result to the actual function decorated by
            :class:`zetup.program`
            """
            args = self.parse_args(sys.argv if argv is None else argv)
            return func(args)

        # give wrapper function same name as wrapped one, since it is the one
        # to be returned here
        caller.__name__ = func.__name__
        if hasattr(func, '__qualname__'):
            caller.__qualname__ = func.__qualname__
        return caller

program.__doc__ = program.__doc__.format(
    zetup_version=zetup.__version__)  # pylint: disable=no-member


class with_arguments(object):
    """
    Gather argument definitions for instances of ``argparse.ArgumentParser``.

    To be used with :class:`zetup.program`, which is derived from the latter

    Initialization and further calling support the same signature as
    ``ArgumentParser.add_argument``. Calls always return the instance itself.
    So all definitions can be chained

    The result direclty passed as first positional argument to
    :class:`zetup.program`, which you should also refer to for a complete
    explanation and example

    The ``with_arguments`` name is btw inspired by ``six.with_metaclass`` :)
    """

    def __init__(self, *args, **kwargs):
        """
        Take same arguments as ``argparse.ArgumentParser.add_argument``.

        Initializes the internal list of argument definitions
        """
        self._list = []
        self(*args, **kwargs)

    def __call__(self, *args, **kwargs):
        """
        Take same arguments as ``argparse.ArgumentParser.add_argument``.

        Works like :meth:`.__init__` and extends the internal list of
        argument definitions
        """
        self._list.append((args, kwargs))
        return self

    def __iter__(self):
        return iter(self._list)
