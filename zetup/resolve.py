# ZETUP
#
# Zimmermann's Extensible Tools for Unified Project setups
#
# Copyright (C) 2014-2017 Stefan Zimmermann <user@zimmermann.co>
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
Resolver for setup requirements, fetching ``.eggs/`` on demand
"""

import re
import sys

import pkg_resources
try:
    from pip._vendor import pkg_resources as pip_vendor_pkg_resources
except ImportError:
    pip_vendor_pkg_resources = None
from pkg_resources import (
    DistributionNotFound, VersionConflict, get_distribution)
from setuptools.dist import Distribution

__all__ = ['resolve']


#: The egg installer
# INSTALLER = Distribution().fetch_build_egg


class StdErrWrapper(object):
    """
    For safely redirecting ``stdout`` to ``stderr``

    For example on Windows, directly assigning ``stderr`` to ``stdout`` often
    leads to a detached ``stderr`` buffer in the end
    """

    def __getattr__(self, name):
        return getattr(sys.__stderr__, name)

    def detach(self):
        """
        Don't let ``stderr``'s buffer get stolen
        """
        return self

    def __del__(self):
        """
        Don't let :meth:`.__getattr__` fetch ``stderr``'s ``.__del__``
        """
        pass


def resolve(requirements):
    """
    Make sure that setup `requirements` are always correctly resolved and
    accessible by:

    - Recursively resolving their runtime requirements
    - Moving any installed eggs to the front of ``sys.path``
    - Updating ``pkg_resources.working_set`` accordingly
    """
    from .pip import pip

    # don't pollute stdout! first backup
    __stdout__ = sys.__stdout__
    stdout = sys.stdout
    # then redirect to stderr...
    sys.stdout = sys.__stdout__ = StdErrWrapper()

    def _resolve(requirements, parent=None):
        """
        The actual recursive `requirements` resolver

        `parent` string is used for printing fully qualified requirement
        chains
        """
        for req in requirements:
            qualreq = parent and '%s->%s' % (req, parent) or req
            print("Resolving setup requirement %s:" % qualreq)
            try:
                dist = get_distribution(req)
            except (DistributionNotFound, VersionConflict) as exc:
                # if isinstance(exc, VersionConflict):
                #     pip.uninstall(re.split(r'\W', req)[0], '--yes')
                #     # pkg_resources._initialize_master_working_set()

                #     # adapt pkg_resources to the newly installed requirement
                #     pkg_resources.working_set = working_set = WorkingSet()
                #     pkg_resources.require = working_set.require
                #     pkg_resources.iter_entry_points = (
                #         working_set.iter_entry_points)

                pip.install(req, '--no-warn-conflicts')
                # pkg_resources._initialize_master_working_set()

                # adapt pkg_resources to the newly installed requirement
                pkg_resources_modules = [pkg_resources]
                if pip_vendor_pkg_resources is not None:
                    pkg_resources_modules.append(pip_vendor_pkg_resources)

                for pkg_r in pkg_resources_modules:
                    pkg_r.working_set = working_set = pkg_r.WorkingSet()
                    pkg_r.require = working_set.require
                    pkg_r.iter_entry_points = working_set.iter_entry_points

                dist = get_distribution(req)
                sys.path.insert(0, dist.location)

            print(repr(dist))

            extras = re.match(r'[^#\[]*\[([^#\]]*)\]', req)
            if extras:
                extras = list(map(str.strip, extras.group(1).split(',')))
            _resolve(
                (str(req).split(';')[0] for req in dist.requires(
                    extras=extras or ())),
                qualreq)

    _resolve((str(req).split(';')[0] for req in requirements))
    # ... and finally restore stdout
    sys.__stdout__ = __stdout__
    sys.stdout = stdout
