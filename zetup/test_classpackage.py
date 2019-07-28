# zetup.py
#
# Zimmermann's Python package setup.
#
# Copyright (C) 2014-2016 Stefan Zimmermann <zimmermann.code@gmail.com>
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

"""
Test :class:`zetup.class_package`.

.. moduleauthor:: Stefan Zimmermann <zimmermann.code@gmail.com>
"""

from __future__ import absolute_import

import pytest

import zetup


def test_deprecated_name():
    with pytest.warns(DeprecationWarning):
        assert zetup.classpackage is zetup.class_package


def test_bases():
    for base in [zetup.object, zetup.package]:
        assert issubclass(zetup.class_package, base)
    for nobase in [zetup.toplevel]:
        assert not issubclass(zetup.class_package, nobase)


def test_metabases():
    assert type(zetup.class_package) is zetup.meta


def test__repr__():
    assert repr(zetup.class_package) == "<class 'zetup.class_package'>"


def test_members():
    # should not contain more members than basic zetup.package
    assert dir(zetup.class_package) == dir(zetup.package)
