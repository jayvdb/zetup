"""Test :mod:`zetup.object`,
   containing basic ``object``-derived class
   and ``type``-derived ``meta`` class.

.. moduleauthor:: Stefan Zimmermann <zimmermann.code@gmail.com>
"""
from itertools import chain

import zetup


class TestMeta(object):
    """Test basic ``type``-derived :class:``zetup.meta``.
    """
    def test_class(self):
        assert issubclass(zetup.meta, type)

    def test_dir(self):
        # check that dir(meta) returns the same as dir(type)
        # (with added '__dir__' in PY2)
        assert set(dir(zetup.meta)) == set(dir(type)).union([
            '__dir__',
            'member', 'metamember',
        ])
        # and that there are no duplicate names
        assert sorted(dir(zetup.meta)) == sorted(set(dir(zetup.meta)))


class TestObject(object):
    """Test basic ``object``-derived :class:``zetup.object``.
    """
    def test_class(self):
        assert type(zetup.object) is zetup.meta

    def test_class_dir(self):
        # check that dir(zetup.object) exactly returns all member names
        # from class and metaclass level,
        # which in this case are all members from builtin object and type
        # and the added '__dir__' in PY2 (and auto-added '__weakref__')
        assert set(dir(zetup.object)) == set(chain(dir(object), dir(type), [
            '__dir__',
            '__package__',
            '__weakref__',
            'member',
            'metamember',
        ]))
        # and that there are no duplicate names
        assert sorted(dir(zetup.object)) == sorted(set(dir(zetup.object)))

    def test_dir(self):
        # check that dir(zetup.object()) only returns all member names
        # from class    level and auto-generated instance member names
        # (but no extra member names from metaclass level),
        # which in this case are all members from a builtin object instance,
        # the added zetup.object.__dir__ in PY2,
        # and auto-added '__weakref__', '__module__' and '__dict__'
        # from zetup.object class level
        assert set(dir(zetup.object())) == set(chain(dir(object()), [
            '__dict__',
            '__dir__',
            '__module__',
            '__package__',
            '__weakref__',
        ]))
