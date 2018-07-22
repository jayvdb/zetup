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

"""zetup.commands.dev

Defines ``zetup dev`` command.

.. moduleauthor:: Stefan Zimmermann <zimmermann.code@gmail.com>
"""
import pip

from zetup.zetup import Zetup
from zetup.pip import pip

from zetup.commands.del_ import del_

__all__ = ['dev']


@Zetup.command(depends=['setup.py'])
def dev(zfg, args=None):
    """Install project in develop mode."""
    # first remove any current project installation
    del_(zfg)
    # then (re)install project in develop mode (and return pip status code)
    source = str(zfg.ZETUP_DIR)
    if zfg.EXTRAS:
        source += '[all]'
    return pip(['install', '--editable', source], raise_=False)
