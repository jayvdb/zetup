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

"""zetup

.. moduleauthor:: Stefan Zimmermann <zimmermann.code@gmail.com>
"""
from __future__ import absolute_import

import sys

import pkg_resources
# pkg_resources might not be fully populated yet during setup of namespaces
pkg_resources.iter_entry_points = pkg_resources.WorkingSet().iter_entry_points
pkg_resources.require = pkg_resources.WorkingSet().require


from .entry_point import setup_entry_point
from .zetup import Zetup, find_zetup_config
from .error import ZetupError
from .config import ZetupConfigNotFound
from .requires import DistributionNotFound, VersionConflict
from .resolve import resolve
from .process import Popen, call
from .object import object, meta
from .annotate import annotate
from .func import apifunction
from .modules import module, package, toplevel, extra_toplevel
from .classes import class_package, class_member_module
from .zfg import ZFG_PARSER, ZFGData, ZFGFile, ZFGParser, parse_zfg
from .pip import ZetupPipError, pip
# import notebook subpackage for defining extra_toplevel below
from . import notebook


zetup = toplevel(__name__, [
    'setup_entry_point',
    'Zetup', 'find_zetup_config',
    'ZetupError', 'ZetupConfigNotFound',
    'ZFG_PARSER', 'ZFGFile', 'ZFGData', 'parse_zfg',
    'resolve', 'DistributionNotFound', 'VersionConflict',
    'Popen', 'call',
    'object', 'meta',
    'annotate', 'apifunction',
    'module', 'package', 'toplevel', 'extra_toplevel',
    'class_package', 'class_member_module',
    'program', 'with_arguments',
], deprecated_aliases={
    'classpackage': 'class_package',
}, check_requirements=False)


from .program import program, with_arguments


# can't be defined in .notebook subpackage
# because .notebook is also needed to load zetup's own config
# which is required for making extra_toplevel instantiation work
extra_toplevel(zetup, notebook.__name__, [
    'Notebook',
], check_requirements=False)
# since actual .notebook subpackage was imported before
# a manually setting of the subpackage attribute
# on the zetup toplevel wrapper is needed
sys.modules[__name__].notebook = sys.modules[notebook.__name__]
