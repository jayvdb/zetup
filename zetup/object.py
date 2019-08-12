# ZETUP | Zimmermann's Extensible Tools for Unified Projects
#
# Copyright (C) 2014-2019 Stefan Zimmermann <user@zimmermann.co>
#
# ZETUP is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# ZETUP is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with ZETUP. If not, see <http://www.gnu.org/licenses/>.

"""
Define basic :class:`zetup.object` and its :class:`zetup.meta`.

For extending builtin ``object`` and ``type`` with useful extra features

.. moduleauthor:: Stefan Zimmermann <user@zimmermann.co>
"""

from __future__ import absolute_import

import sys
from inspect import ismodule
from itertools import chain

import zetup

__all__ = ('object', 'meta')


class meta(type):
    """
    Basic metaclass that extends builtin ``type`` with useful extra features.

    Adds a unified basic ``__dir__`` method for Python 2 and 3, which always
    returns all member names from metaclass and class level

    Adds :meth:`.metamethod` and :meth:`.method` decorators for adding new
    members to classes and their metaclasses outside of the class definition
    scopes
    """

    def __init__(cls, clsname, bases, clsattrs):
        super(meta, cls).__init__(clsname, bases, clsattrs)
        if '__package__' not in clsattrs:
            cls.__package__ = None

    if hasattr(type, '__dir__'):  # PY3
        def __dir__(cls):
            """Get all member names from class and metaclass level."""
            return sorted(set(chain(type.__dir__(cls), dir(type(cls)))))

    else:  # PY2
        def __dir__(cls):
            """Get all member names from class and metaclass level."""
            return sorted(set(chain(
                dir(type(cls)), *(c.__dict__ for c in cls.mro()))))

    @classmethod
    def metamember(mcs, obj):
        """
        Decorator for adding `obj` as a member to the metaclass of this class.

        >>> import six  # if you want compatibility with Python 2 and 3
        >>> import zetup

        This is of course only useful when you have a custom metaclass:

        >>> class Meta(zetup.meta):
        ...     pass

        Now you can add new members to your custom metaclass outside of the
        class definition scope:

        >>> @Meta.metamember
        ... def method(cls, arg):
        ...     pass

        >>> Meta.method
        <... Meta.method...>

        This also works from a new class based on this metaclass. In Python 3
        syntax you create such a class like::

            class Class(zetup.object, metaclass=Meta):
                pass

        But if you want to be compatible with Python 2 and 3:

        >>> class Class(six.with_metaclass(Meta, zetup.object)):
        ...     pass

        >>> @Class.metamember
        ... def another_method(cls, arg):
        ...     pass

        >>> Meta.another_method
        <... Meta.another_method...>

        >>> Class.another_method
        <bound method Meta.another_method of ...Class...>

        And the formerly defined ``@Meta.metamember`` is of course also there:

        >>> Class.method
        <bound method Meta.method of ...Class...>
        """
        if isinstance(obj, property):
            name = obj.fget.__name__
        else:
            try:
                name = obj.__name__
            except AttributeError:
                name = obj.__func__.__name__
            else:
                obj.__qualname__ = '%s.%s' % (
                    getattr(mcs, '__qualname__', mcs.__name__),
                    obj.__name__)
        setattr(mcs, name, obj)
        return obj

    def member(cls, obj):
        """
        Decorator for adding `obj` as a member to this class.

        >>> import zetup

        >>> class Class(zetup.object):
        ...     pass

        Now you can add new members to your class outside of the class
        definition scope:

        >>> @Class.member
        ... def method(self, arg):
        ...     pass

        >>> Class.method
        <... Class.method...>

        >>> Class().method
        <bound method Class.method of ...Class...>
        """
        if isinstance(obj, property):
            name = obj.fget.__name__
        else:
            try:
                name = obj.__name__
            except AttributeError:
                name = obj.__func__.__name__
            else:
                obj.__qualname__ = '%s.%s' % (
                    getattr(cls, '__qualname__', cls.__name__),
                    obj.__name__)
        setattr(cls, name, obj)
        return obj

    def __str__(cls):
        clsname = getattr(cls, '__qualname__', cls.__name__)
        mod = getattr(cls, '__package__', None) or cls.__module__
        if ismodule(mod):  # (and not just a string)
            mod = mod.__name__  # pylint: disable=no-member
        elif mod is None:
            return clsname

        return '.'.join((mod, clsname))

    def __repr__(cls):
        """Create PY2/3 unified PY3-style representation."""
        return "<class {!r}>".format(str(cls))


# PY2/3 compatible way to create class `object` with metaclass `meta`...

def __repr__(self):
    """Create PY2/3-unified PY3-style representation."""
    return "<{} at {}>".format(type(self), hex(id(self)).rstrip('L'))

clsattrs = {
    '__package__': zetup,
    '__doc__': """
    Basic class that extends builtin ``object`` with useful extra features.

    Adds a basic ``__dir__`` method for Python 2

    Has :class:`zetup.meta` as metaclass and therefore provides
    :meth:`zetup.meta.metamethod` and :meth:`zetup.meta.method` decorators for
    adding new members to classes and their metaclasses outside of the class
    definition scopes
    """,
    '__repr__': __repr__}

if not hasattr(object, '__dir__'):

    def __dir__(self):
        """Get all member names from instance and class level."""
        return sorted(set(chain(
            self.__dict__,
            *(c.__dict__ for c in type(self).mro()))))

    clsattrs['__dir__'] = __dir__

object = meta('object', (object, ), clsattrs)
