# ZETUP | Zimmermann's Extensible Tools for Unified Project_setups
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
Several ``module`` object wrappers.

For modules, packages, top-level packages, and top-level packages for extra
features

.. moduleauthor:: Stefan Zimmermann <zimmermann.code@gmail.com>
"""

from __future__ import absolute_import

import sys
from importlib import import_module
from inspect import ismodule
from itertools import chain
from types import ModuleType
from warnings import warn

import zetup
from .object import object, meta
from .annotate import annotate, annotate_extra
from .doc import AutoDocScopeModule

__all__ = ('package', 'toplevel')


class deprecated(str):
    """
    Simple ``str`` class wrapper for indicating deprecation.

    Marks a :class:`zetup.package` API member (alias) name as deprecated
    """
    def __repr__(self):
        return "deprecated(%s)" % str.__repr__(self)


class package(ModuleType, object):
    """
    Package module object wrapper.

    Providing clean dynamic API imports from sub-modules
    """

    __package__ = zetup

    def __init__(
            self, name, __all__=None,
            aliases=None, deprecated_aliases=None,
            __getitem__=None, __iter__=None, __call__=None):
        """
        Wrap a package module given by `name`.

        Original package module object is replaced in ``sys.modules`` and
        stored in :attr:``.__module__``

        Optional `__all__` list defines the package API

        Optional `aliases` and `deprecated_aliases` map alternative names to
        API names

        `__getitem__`, `__iter__`, and `__call__` features can be added to the
        package wrapper by providing handler functions or other callable
        objects (which are not called with a ``self`` argument)
        """
        mod = sys.modules[name]
        ModuleType.__init__(  # pylint: disable=no-member
            self, name, mod.__doc__)
        self.__name__ = name
        self.__module__ = mod
        sys.modules[name] = self

        self.__dict__['__all__'] = api \
            = dict.fromkeys(__all__) if __all__ is not None else {}
        if aliases is not None:
            api.update(aliases)
        if deprecated_aliases is not None:
            api.update(
                (deprecated(alias), name)
                for alias, name in dict(deprecated_aliases).items())

        # if api is not None:
        #     for submodname, members in dict(__all__).items():
        #         self.__dict__['__all__'].update(
        #             (name, submodname) for name in members)

        cls = type(self)
        cls.__getitem__.funcs[self] = __getitem__
        cls.__iter__.funcs[self] = __iter__
        cls.__call__.funcs[self] = __call__

    def __getitem__(self, key):
        cls = type(self)
        func = cls.__getitem__.funcs.get(self)
        if func is None:
            raise TypeError(
                "%s is not subscriptable. "
                "Instantiate %s with __getitem__=<func> to change that."
                % (repr(self), repr(cls)))

        return func(key)

    __getitem__.funcs = {}

    def __iter__(self):
        cls = type(self)
        func = cls.__iter__.funcs.get(self)
        if func is None:
            raise TypeError(
                "%s is not iterable. "
                "Instantiate %s with __iter__=<func> to change that."
                % (repr(self), repr(cls)))

        return func()

    __iter__.funcs = {}

    def __call__(self, *args, **kwargs):
        cls = type(self)
        func = cls.__call__.funcs.get(self)
        if func is None:
            raise TypeError(
                "%s is not callable. "
                "Instantiate %s with __call__=<func> to change that."
                % (repr(self), repr(cls)))

        return func(*args, **kwargs)

    __call__.funcs = {}

    @property
    def __all__(self):
        """Get API names list (without deprecated aliases)."""
        return list(set(chain(
            getattr(self.__module__, '__all__', ()), (
                name for name in self.__dict__['__all__']
                if not isinstance(name, deprecated)))))

    def __setattr__(self, name, value):
        """
        Prevent submodules from being added as attributes.

        To avoid unnecessary ``dir()`` pollution
        """
        if isinstance(value, AutoDocScopeModule) or ismodule(value) and (
                value.__name__ == '%s.%s' % (self.__name__, name) and
                not isinstance(value, package)):
            return

        from .classpackage import classpackage
        if isinstance(value, classpackage):
            value = getattr(value, name)
        object.__setattr__(self, name, value)

    def __getattribute__(self, name):
        """Dynamically access API from wrapped module or import extra API."""
        if name.startswith('__'):
            try:
                return object.__getattribute__(self, name)
            except AttributeError:
                pass

        # check if name is defined as alias
        realname = self.__dict__['__all__'].get(name)
        if realname is not None:
            if isinstance(name, deprecated):
                warn("%s.%s is deprecated in favor of %s.%s" % (
                    self.__name__, name, self.__name__, realname
                ), DeprecationWarning)
            name = realname

        try:  # first try to get attr from wrapped original module
            return getattr(self.__module__, name)

        except AttributeError:
            try:  # then from wrapper module
                obj = self.__dict__[name]
            except KeyError:
                if name in getattr(self.__module__, '__all__', ()):
                    raise AttributeError(
                        "%s has no attribute %s although listed in __all__"
                        % (repr(self.__module__), repr(name)))

            try:  # and finally try to find a matching submodule
                # sys.modules[self.__name__] = self.__module__
                # __import__('ipdb').set_trace()
                obj = import_module('%s.%s' % (self.__name__, name))
            except ImportError as exc:
                raise AttributeError(
                    "%s has no attribute %s" % (repr(self), repr(name)))

            # finally:
            #     sys.modules[self.__name__] = self

        if isinstance(obj, zetup.classpackage):
            classobj = getattr(obj, name)
            setattr(self, name, classobj)
            return classobj

        return obj

    def __dir__(self):
        """Additionally get all API member names."""
        def exclude():
            """
            Get names of submodules implicitly added to ``__dict__``.

            Which happens on ``from .submodule import ...`` statements in
            wrapped module following the wrapper instantiation
            """
            for name, obj in self.__dict__.items():
                if name.startswith('__'):
                    continue

                if ismodule(obj) and not isinstance(obj, package):
                    yield name

        return list(chain(
            # (
            #     name for name in self.__module__.__dict__
            #     if name.startswith('__')),
            set(
                object.__dir__(self)  # pylint: disable=no-member
            ).difference(exclude()),
            self.__all__))

    def __repr__(self):
        """Create module-style representation."""
        return "<%s %s from %s>" % (
            type(self).__name__, repr(self.__name__),
            repr(self.__module__.__file__))


class toplevel(package):
    """
    Special top-level package module object wrapper.

    For clean dynamic API import from sub-modules and automatic application
    of func:`zetup.annotate`
    """

    __package__ = zetup

    def __init__(
            self, name, __all__=None,
            aliases=None, deprecated_aliases=None,
            check_requirements=True, check_packages=True,
            __getitem__=None, __iter__=None, __call__=None):
        """
        Wrap top-level package module given by `name` and `api` list.

        See :class:`zetup.package` for details about defining the package
        API and special features

        See :func:`zetup.annotate` for details about the check options
        """
        super(toplevel, self).__init__(
            name, __all__,
            aliases=aliases, deprecated_aliases=deprecated_aliases,
            __getitem__=__getitem__, __iter__=__iter__, __call__=__call__)

        zfg = annotate(
            name, check_requirements=check_requirements,
            check_packages=check_packages)
        self.__package__ = pkg = zfg.PACKAGES[name]
        pkg.zetup_config = zfg


class extra_toplevel_meta(meta):
    """Metaclass for :class:`zetup.extra_toplevel`."""

    extra = None

    def __getitem__(cls, extra):
        mcs = type(cls)
        meta = type('%s[%s]' % (mcs.__name__, extra), (mcs, ), {
            'extra': extra,
        })
        return meta('%s[%s]' % (cls.__name__, extra), (cls, ), {})


class extra_toplevel(
        # PY2/3 compatible way to assign metaclass
        extra_toplevel_meta('extra_toplevel_base', (package, ), {})):
    """
    Special extra feature top-level package module object wrapper.

    For clean dynamic API import from sub-modules and automatic application
    of func:`zetup.annotate_extra`
    """

    __package__ = zetup

    def __init__(
            self, toplevel, name, __all__=None,
            aliases=None, deprecated_aliases=None,
            check_requirements=True,
            __getitem__=None, __iter__=None, __call__=None):
        """
        Wrap top-level package module given by `name` and `api` list.

        See :class:`zetup.package` for details about defining the package
        API and special features

        See :func:`zetup.annotate_extra` for details about the check option
        """
        super(extra_toplevel, self).__init__(
            name, __all__,
            aliases=aliases, deprecated_aliases=deprecated_aliases,
            __getitem__=__getitem__, __iter__=__iter__, __call__=__call__)

        extra = type(self).extra
        annotate_extra[extra](  # pylint: disable=unsubscriptable-object
            toplevel, name, check_requirements=check_requirements)
