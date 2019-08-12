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

"""Define :class:`zetup.class_package`."""

from __future__ import absolute_import

from importlib import import_module

import zetup

__all__ = ('class_package', )


class class_package(zetup.package):
    """
    Module wrapper for a sub-package that defines a huge class.

    Enables auto-import of the class object instead of the package module
    object when imported from its parent package, and supports the
    distribution of class member definitions in separate sub-modules, given
    the following conditions:

    -   The class is named after the sub-package
    -   The class is a sub-class of :class:`zetup.object`
    -   The name of the sub-package containing the class is defined as API
        member of a parent :class:`zetup.package` instance
    -   All sub-module names are listed in the ``member_modules=`` argument,
        and members in those sub-modules are decorated using
        :meth:`zetup.meta.member` and `:meth:`zetup.meta.metamember`, which
        can be obtained from the :class:`zetup.class_member_module` wrapper

    The whole mechanism is shown below using the example ``Class`` contained
    in the ``zetup.classes.test`` package:

    ``zetup/classes/test/__init__.py`` ::

        import zetup
        zetup.package(__name__, ['Class', ...])

    ``zetup/classes/test/Class/__init__.py`` ::

        import zetup
        zetup.class_package(__name__, member_modules=['methods', ...])

        class Class:
            def __init__(self, ...):
                ...
            ...

    ``zetup/classes/test/Class/methods.py`` ::

        import zetup
        member, metamember = zetup.class_member_module(__name__ ['method'])

        @member
        def method(self, ...):
            ...

    >>> from zetup.classes.test import Class
    >>> Class
    <class 'zetup.classes.test.Class'>
    >>> Class.method
    <... Class.method...>
    """

    __package__ = zetup

    def __init__(self, pkgname, member_modules=None):
        """Created with ``__name__`` of the subpackage defining the class
        and the optional list of `membermodules` to automatically import
        (sub-modules defining additional class members).
        """
        parentpkgname, classname = pkgname.rsplit('.', 1)
        super(class_package, self).__init__(pkgname, [classname])

        pkgcls = type(self)
        pkgdict = self.__dict__

        def load_class():
            """Get the actual class object from this class package
            and automatically import all defined ``membermodules``.
            """
            classobj = pkgcls.__getattribute__(self, classname)
            if not getattr(classobj, '__package__', None):
                classobj.__package__ = parentpkgname
            if member_modules is not None:
                for modname in member_modules:
                    mod = import_module('%s.%s' % (pkgname, modname))
                    mod.owner = classobj
            return classobj

        class package(type(self)):
            """Help tools like sphinx ``.. autoclass::`` doc generator
            by delegating (almost) all attributes to the actual class object.

            * ``.. autoclass:: package.Class`` first looks up
              ``package.Class`` in imported modules and therefore
              doesn't get the actual class object itself.
            """
            def __getattribute__(self, name):
                if name == classname:
                    # get the actual class object
                    try:
                        return pkgdict[classname]
                    except KeyError:
                        # only load once
                        classobj = pkgdict[classname] = load_class()
                        return classobj
                # only take these few special attributes
                # from the classpackage instance itself
                if name in [
                        '__name__', '__all__',  '__module__', '__path__',
                        '__file__', '__class__', '__dict__',
                ]:
                    return pkgcls.__getattribute__(self, name)
                # and take all other attributes from the class object
                # (by first recursively calling this __getattribute__)
                return getattr(getattr(self, classname), name)

            def __repr__(self):
                return "<%s for %s from %s>" % (
                    pkgcls.__name__, repr(getattr(self, classname)),
                    repr(self.__file__))

        self.__class__ = package
