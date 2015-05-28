# zetup.py
#
# Zimmermann's Python package setup.
#
# Copyright (C) 2014-2015 Stefan Zimmermann <zimmermann.code@gmail.com>
#
# zetup.py is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# zetup.py is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with zetup.py. If not, see <http://www.gnu.org/licenses/>.

import os
from glob import glob
from textwrap import dedent


class File(str):
    """The name of a package file (source or data)
       with reference to the package and its absolute path.
    """
    def __new__(cls, name, package):
        return str.__new__(cls, name)

    def __init__(self, name, package):
        self.package = package

    @property
    def path(self):
        return os.path.join(self.package.path, self)


class Source(File):
    """The name of a package *.py source file
       with reference to the package and its absolute path.
    """
    pass


class DataFile(File):
    """The name of a package data file
       with reference to the package and its absolute path.
    """
    pass


class Package(str):
    """Package name wrapper with access to
       package path, source files, package data and subpackages,
       and validation features for installed packages.
    """
    def __new__(cls, pkg, **kwargs):
        return str.__new__(cls, pkg)

    def __init__(self, pkg, root=None, path=None,
                 sources=None, data=None, subpackages=None):
        if not isinstance(pkg, Package):
            pkg = None
        self.root = root or pkg and pkg.root
        self._path = path or pkg and pkg._path
        self._sources = sources and list(sources) \
          or pkg and pkg._sources or None
        self.data = data and list(data) or pkg and pkg.data or None
        self._subpackages = subpackages and list(subpackages) \
          or pkg and pkg._subpackages or None

    @property
    def path(self):
        """The absolute path of the package.
        """
        return os.path.realpath(os.path.join(self.root or '.',
          self._path or os.path.join(*self.split('.'))))

    def sources(self):
        """Iterates :class:`zetup.package.Source` instances
           absolute of the package's direct source *.py files
           (without sub-package sources).
        """
        # sources = self.__dict__.get('sources')
        # if sources:
        #     for path in sources:
        #         yield path
        #     return

        for name in os.listdir(self.path):
            path = os.path.join(self.path, name)
            if os.path.isfile(path) and path.endswith('.py'):
                yield Source(name, package=self)

    def datafiles(self):
        """Iterates :class:`zetup.package.DataFile` instances
           of the package's direct data files
           (without sub-package data files).
        """
        if not self.data:
            return
        for pattern in self.data:
            for path in glob(os.path.join(self.path, pattern)):
                yield DataFile(os.path.relpath(path, self.path),
                               package=self)

    def files(self):
        """Iterates the package's direct sources and data files combined
           (without sub-package files).
        """
        for path in self.sources():
            yield path
        for path in self.datafiles():
            yield path

    def walksources(self):
        """Recursively iterates the source *.py files of the package
           and its sub-packages.
        """
        for path in self.sources():
            yield path
        for pkg in self.subpackages():
            for path in pkg.walksources():
                yield path

    def walkdatafiles(self):
        """Recursively iterates the data files of the package
           and its sub-packages.
        """
        for path in self.datafiles():
            yield path
        for pkg in self.subpackages():
            for path in pkg.walkdatafiles():
                yield path

    def walkfiles(self):
        """Recursively iterates the source and data files of the package
           and its sub-packages.
        """
        for path in self.files():
            yield path
        for pkg in self.subpackages():
            for path in pkg.walkfiles():
                yield path

    def subpackages(self):
        """Iterates the package's direct sub-packages as instances of own type
           (without sub-sub-packages).
        """
        # subpkgs = self.__dict__.get('subpackages')
        # if subpkgs:
        #     for pkg in subpkgs:
        #         yield pkg
        #     return

        for name in os.listdir(self.path):
            path = os.path.join(self.path, name)
            if os.path.isdir(path) and os.path.isfile(
              os.path.join(path, '__init__.py')):
                yield type(self)('.'.join((self, name)))

    def walksubpackages(self):
        """Iterates the package's sub-packages recursively.
        """
        for pkg in self.subpackages():
            yield pkg
            for subpkg in pkg.walksubpackages():
                yield subpkg

    def __getitem__(self, name):
        """Get a subpackge by its relative name.
        """
        for pkg in self.subpackages():
            if pkg == '.'.join((self, name)):
                return pkg
        raise KeyError("%s has no sub-package named %s"
                       % (repr(self), repr(name)))

    def __getattr__(self, name):
        """Fast interactive way for the shell
           to get a subpackge by its relative name.
        """
        try:
            return self[name]
        except KeyError:
            raise AttributeError(
              "%s has no attribute or sub-package named %s"
              % (repr(self), repr(name)))

    def check(self, raise_=True):
        sources = getattr(self, '_sources', None)
        if sources is not None:
            diff = set(sources) - set(self.sources())
            if diff:
                if raise_:
                    raise RuntimeError(diff)
                return False

        subpkgs = getattr(self, '_subpackages', None)
        if subpkgs is not None:
            diff = set(subpkgs) - set(self.subpackages())
            if diff:
                if raise_:
                    raise RuntimeError
                return False

        return True

    @property
    def py(self):
        """Generate Python code for zetup config module.
        """
        return dedent("""
          %s(%s,
            sources=[
              %s
              ],
            subpackages=[
              %s
              ],
            )
          """) % (type(self).__name__, repr(str(self)),
                  ",\n    ".join(repr(os.path.basename(src)) for src in self.sources()),
                  ",\n    ".join(pkg.py for pkg in self.subpackages()))


class Packages(object):
    def __init__(self, toplevel, root=None):
        self.toplevel = [Package(name, root=root) for name in toplevel]

    def __iter__(self):
        """Iterate all toplevel and sub-packages.
        """
        for pkg in self.toplevel:
            yield pkg
            for subpkg in pkg.walksubpackages():
                yield subpkg

    def __len__(self):
        return len(list(iter(self)))

    def __getitem__(self, name):
        for pkg in self:
            if pkg == name:
                return pkg
        raise KeyError("No package named %s" % repr(name))

    def __getattr__(self, name):
        try:
            return self[name]
        except KeyError:
            raise AttributeError(
              "%s instance has no attribute or package named %s"
              % (type(self), repr(name)))

    def __bool__(self):
        """Any packages?
        """
        return bool(self.toplevel)

    #PY2
    def __nonzero__(self):
        return self.__bool__()

    @property
    def main(self):
        return next(iter(self))

    def check(self, raise_=True):
        for pkg in self:
            pkg.check(raise_=raise_)

    @property
    def checked(self):
        self.check()
        return self

    @property
    def py(self):
        """Generate Python code for zetup config module.
        """
        return "%s([\n%s\n  ])" % (type(self).__name__, ",\n  ".join(
          pkg.py for pkg in self.toplevel))

    def __repr__(self):
        return "%s(%s)" % (type(self).__name__, repr(self.toplevel))
