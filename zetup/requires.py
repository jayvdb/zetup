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

import re
import sys
from textwrap import dedent

import pkg_resources
from pkg_resources import (
    parse_requirements, Requirement, get_distribution)

__all__ = (
    'DistributionNotFound',
    'Requirements',
    'VersionConflict',
    'requires',
)


if sys.version_info[0] == 3:
    unicode = str


def howto_install_requirement(req):
    """Create a message explaining how to install `req`"""
    return dedent("""
    You can install the needed requirement with the following shell command:

        python -m pip install "{}"
    """.format(req)).strip()


class DistributionNotFound(pkg_resources.DistributionNotFound):

    def __init__(self, req, requirer, reason=None):
        super(DistributionNotFound, self).__init__(req, [requirer])
        self.requirer = requirer
        self.reason = reason

    def __str__(self):
        text = "%s needs %s" % (self.requirer, self.req)
        if self.reason:
            text += " (%s)" % self.reason
        return "{}\n\n{}".format(text, howto_install_requirement(self.req))


class VersionConflict(pkg_resources.VersionConflict):

    def __init__(self, req, found_version, requirer, reason=None):
        super(VersionConflict, self).__init__(
            '%s-%s' % (req.key, found_version), req)
        self.requirer = requirer
        self.reason = reason

    def __str__(self):
        text = "%s needs %s but found %s" % (
            self.requirer, self.req, self.dist)
        if self.reason:
            text += " (%s)" % self.reason
        return "{}\n\n{}".format(text, howto_install_requirement(self.req))


class Requirements(object):
    """Package requirements manager."""

    @staticmethod
    def _parse(text):
        """
        Generate parsed requirements from `text`.
        
        :param text:
            Newline-separated requirement specs

        Additionally looks for ``#import name`` comments after requirement
        lines (the actual root module name of the required package to use for
        runtime dependency checks) and stores them as .impname attrs on the
        Requirement instances.

        Supports ``#py..`` tags at the beginning of lines, specifying a python
        version the requirement applies to.
        """
        for line in text.split('\n'):
            line = line.strip()
            if not line:
                continue
            match = re.match(r'^#py([0-9]+) (.*)$', line)
            if match: #==> only required in given python version
                pyver, line = match.groups()
                #TODO:
                # if len(pyver) > 2:
                if not ('%s%s' % sys.version_info[:2]).startswith(pyver):
                    continue
            try:
                req, impname = line.split('#import')
            except ValueError:
                req = next(parse_requirements(line), None)
                impname = req and req.unsafe_name
            else:
                req = next(parse_requirements(req), None)
            if not req: # maybe a comment line
                continue
            req.impname = impname.strip()
            yield req

    def __init__(self, reqs, zfg=None):
        """
        Generate a list of :class:`pkg_resources.Requirement` instances.

        And additionally store all requirement specs as text with newline
        separators in the ``str`` base

        :param reqs:
            Either a single string of requirement specs or a sequence of
            strings and/or :class:`pkg_resources.Requirement` instances
        :param zfg:
            Optional zetup config object the requirements are related to
        """
        if isinstance(reqs, Requirements):
            txt = reqs.txt
            reqlist = list(self._parse(reqs.txt))
        elif isinstance(reqs, (str, unicode)):
            txt = reqs
            reqlist = list(self._parse(reqs))
        else:
            txt = ''
            reqlist = []
            for req in reqs:
                if isinstance(req, (str, unicode)):
                    reqlist.extend(self._parse(req))
                elif isinstance(req, Requirement):
                    reqlist.append(req)
                else:
                    raise TypeError(type(req))
                txt += '\n%s' % req

        self.txt = txt
        self._list = reqlist
        self.zfg = zfg

    def __eq__(self, other):
        return isinstance(other, Requirements) and (
            self._list == other._list)

    def __str__(self):
        return '\n'.join(map(str, self))

    def check(self, requirer=None, raise_=True):
        """
        Check that all requirements are satisfied.
        
        They must be importable and their versions (from their top-level
        package modules' ``.__version__`` attributes) must match the required
        specs

        Falls back to ``pkg_resources.get_distribution().version`` if
        ``.__version__`` is missing or ``None``

        :param requirer:
            Optional identification string of the requirer
        :param raise_:
            If set to ``False`` then also just return ``False`` on unsatisfied
            requirements instead of raising exceptions

        :raises zetup.DistributionNotFound:
            If a requirement can't be imported
        :raises zetup.VersionConflict:
            If a required version doesn't match
        """
        if requirer is None:
            requirer = self.zfg and '%s-%s' % (
                self.zfg.NAME, self.zfg.VERSION or '(none)')
        for req in self:
            try:
                mod = __import__(req.impname)
            except ImportError as e:
                if raise_:
                    raise DistributionNotFound(
                        req, requirer,
                        reason="%s: %s" % (type(e).__name__, e))

                return False

            if not req.specs:  # No version constraints
                continue

            try:
                version = mod.__version__
                if version is None or version == 'unknown':
                    # treat the same as if .__version__ not exists
                    # (handle in following except block)
                    # ==> same exception, just different msg
                    raise AttributeError(
                        "module's '__version__' attribute is {!r}"
                        .format(version))

            except AttributeError as e_no__version__attr:
                try:  # try to get version from distribution
                    dist = get_distribution(req.key)
                except pkg_resources.DistributionNotFound as e:
                    if raise_:
                        raise VersionConflict(
                            req, None, requirer,
                            reason="%s: %s. %s: %s" % (
                                e_no__version__attr, mod, type(e).__name__, e))

                    return False

                version = dist.version
            if version not in req:
                if raise_:
                    raise VersionConflict(req, version, requirer)

                return False

        return True

    @property
    def checked(self):
        self.check()
        return self

    def __iter__(self):
        return iter(self._list)

    def __getitem__(self, name):
        """Get a requirement by its distribution name."""
        for req in self._list:
            if name in [req.key, req.unsafe_name]:
                return req

        raise KeyError(name)

    def __delitem__(self, name):
        """Delete a requirement by its distribution name."""
        for req in list(self._list):
            if name in [req.key, req.unsafe_name]:
                return self._list.remove(req)

        raise KeyError(name)

    def __add__(self, reqs):
        """
        Create a new :class:`Requirements` instance.

        :param reqs:
            Additional requirements as string or another :class:`Requirements`
            instance
        """
        if isinstance(reqs, Requirements):
            reqs = reqs.txt
        return type(self)('%s\n%s' % (
            # For simplicity:
            # Just create explicit #import hints for every requirement:
            # '\n'.join('%s #import %s' % (req, req.impname) for req in self),
            self.txt, reqs), zfg=self.zfg)

    @property
    def py(self):
        return '%s("""\n%s\n""", zfg=zfg)' % (
            type(self).__name__, self.txt)  # '\n'.join(
            # '%s #import %s' % (req, req.impname) for req in self))

    def __repr__(self):
        return str(self)


def requires(reqs):
    """
    Create a function decorator for defining extra requirements.

    :param reqs:
        Requirement specs compatible with :class:`zetup.Requirements` 

    >>> @requires("not-installed")
    ... def func():
    ...     pass

    The actual requirements check happens only on calling the function:

    >>> func()  # doctest: +IGNORE_EXCEPTION_DETAIL
    Traceback (most recent call last):
    ...
    DistributionNotFound: ...func() needs not-installed ...
    <BLANKLINE>
    You can install the needed requirement with the following shell command:
    <BLANKLINE>
        pip install "not-installed"
    """
    reqs = Requirements(reqs)

    def deco(func):

        def caller(*args, **kwargs):
            reqs.check(requirer='{}.{}()'.format(
                func.__module__, func.__name__))
            return func(*args, **kwargs)

        return caller

    return deco
