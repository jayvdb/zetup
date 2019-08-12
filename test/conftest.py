"""Common fixtures for zetup tests.

.. moduleauthor:: Stefan Zimmermann <zimmermann.code@gmail.com>
"""
from inspect import ismodule

from path import Path

import zetup
from zetup import find_zetup_config

import pytest


@pytest.fixture(scope='module')
def zfg():
    """Get zetup's own config.
    """
    return find_zetup_config('zetup')


@pytest.fixture(scope='module')
def in_site_packages(zfg):
    """Is zetup imported from repository?
    """
    return ismodule(zfg)


@pytest.fixture(scope='module')
def in_repo(in_site_packages):
    """Is zetup imported from repo?
    """
    return not in_site_packages


@pytest.fixture(scope='module')
def pkg_path():
    """The dir path of the zetup package.
    """
    return Path(zetup.__file__).realpath().dirname()


@pytest.fixture(scope='module')
def zfg_path(zfg, in_repo, in_site_packages):
    """The dir path of the zetup config.
    """
    if in_repo:
        return Path(zfg.ZETUP_DIR).realpath()
    if in_site_packages:
        return Path(zfg.__file__).realpath().dirname()


@pytest.fixture(scope='module')
def notebook(zfg, in_repo, in_site_packages):
    """zetup's own README.ipynb as :class:`zetup.Notebook` instance
       from zetup's own config.
    """
    if in_site_packages:
        # notebooks aren't installed
        assert 'NOTEBOOKS' not in dir(zfg)
        return None

    return zfg.NOTEBOOKS['README']
