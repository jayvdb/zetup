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

"""zetup.commands.delete

Defines ``zetup del`` command.

.. moduleauthor:: Stefan Zimmermann <zimmermann.code@gmail.com>
"""
import sys
import os

import pkg_resources

from path import Path

from zetup.zetup import Zetup
from zetup.commands.command import command
from zetup.conda import conda
from zetup.pip import pip

__all__ = ('del_', )


@Zetup.command(name='del')
@command(name='del')
def del_(zfg, args=None):
    """Delete project from python environment."""
    try:  # check for conda
        conda_info = conda.info()
    except OSError:  # ==> no conda
        pass
    else:
        # are we in a conda environment?
        if any(
                Path(conda_info[key]).samefile(sys.prefix)
                for key in ['root_prefix', 'default_prefix']
        # and is project installed via conda?
        ) and conda.list('--no-pip', '--full-name', zfg.NAME):
            # then also remove it via conda
            status = conda.remove(zfg.NAME, json=False)
            if status:  # ==> error
                return status
    # is there some project (develop) install (left) to be removed via pip?
    while True:
        try:
            # always use a refreshed working set
            # (interface to installed python package distributions)
            dist = pkg_resources.WorkingSet().by_key[zfg.NAME]
        except KeyError:  # ==> nothing left to uninstall
            break
        status = pip(['uninstall', zfg.NAME, '--yes'], raise_=False)
        if status:  # ==> error
            return status
        root = Path(dist.location)
        if root.exists() and root.samefile(zfg.ZETUP_DIR):
            # pip doesn't remove local .egg-info/ dirs of develop installs
            egg_info = Path(dist._provider.egg_info).realpath()
            print("zetup: Removing %s%s" % (egg_info, os.path.sep))
            egg_info.rmtree()
