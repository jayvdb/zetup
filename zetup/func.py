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

from __future__ import absolute_import

import sys
from inspect import ismodule
try:
    from inspect import signature
except ImportError:
    def signature(func):
        return ""

import zetup
from .object import object

__all__ = ('apifunction', )


class apifunction(object):

    __package__ = zetup.__package__

    def __init__(self, pkg, func=None):
        if not ismodule(pkg):
            raise TypeError(
                "{!r} must be initialized with a module object as first arg"
                ", not {!r}".format(type(self), pkg))

        if func is None:
            self.__package__ = pkg
        else:
            self.__package__ = pkg.__name__
            self.__module__ = func.__module__
            self.__class__ = type('apifunction', (type(self), ), {
                '__doc__': "", '__call__': staticmethod(func)})
            self.__func__ = func

            mod = sys.modules[self.__module__]
            if not hasattr(mod, '__test__'):
                mod.__test__ = {}
            mod.__test__[func.__name__] = func.__doc__

    def __call__(self, func):
        return type(self)(self.__package__, func)

    def __getattr__(self, name):
        if '__func__' in self.__dict__:
            try:
                return getattr(self.__func__, name)

            except AttributeError:
                pass
        raise AttributeError(
            "{!r} has no attribute {!r}".format(self, name))

    def __str__(self):
        if '__func__' in self.__dict__:
            return '.'.join((self.__package__, getattr(
                self.__func__, '__qualname__', self.__func__.__name__)))

        return repr(self)

    def __repr__(self):
        if '__func__' in self.__dict__:
            return "<{} {}.{}{}>".format(
                type(self).__name__, self.__package__, getattr(
                    self.__func__, '__qualname__', self.__func__.__name__),
                signature(self.__func__))

        return "<{} decorator for {!r}>".format(
            type(self), self.__package__)
