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

"""The actual manangement of a project's ``zetup_config``."""

from __future__ import absolute_import

import sys
import os
from importlib import import_module
from subprocess import call
try:
    from setuptools import setup, Command
except ImportError:  # fallback
    # (setuptools should at least be available after package installation)
    from distutils.core import setup, Command

from .config import load_zetup_config, ZetupConfigNotFound

__all__ = ('Zetup', 'find_zetup_config')


class Zetup(object):

    def __init__(self, ZETUP_DIR='.'):
        """Load and store zetup config from `ZETUP_DIR`
           as attributes in `self`.
        """
        load_zetup_config(ZETUP_DIR, zfg=self)

    @property
    def config(self):
        """Get the zetup config as dictionary.

        - Actually just return self.__dict__ because all attr assignments
          come from :func:`.config.load_zetup_config` in :meth:`.__init__`
          and are therefore just the config.
        """
        return self.__dict__

    def __getitem__(self, name):
        return self.config[name]

    @property
    def config_py(self):
        """Get the zetup config as Python code for writing to a .py module.
        """
        def items():
            # always start with project name
            yield "NAME = %s" % (repr(self.config['NAME']))
            for name, value in self.config.items():
                if name in [
                        'NAME', 'NOTEBOOKS',
                ] or name.startswith('ZETUP') or name.endswith('FILE'):
                    continue
                try:
                    py = value.py
                except AttributeError:
                    py = repr(value)
                yield "%s = %s" % (name, py)

        return '\n\n'.join(items())

    def setup_keywords(self):
        """Get a dictionary of `setup()` keywords generated from zetup config.
        """
        keywords = {
            'name': self.NAME,
            'description': self.DESCRIPTION,
            'author': self.AUTHOR,
            'author_email': self.EMAIL,
            'url': self.URL,
            'license': self.LICENSE,
            'setup_requires': str(self.SETUP_REQUIRES or ''),
            'install_requires': str(self.REQUIRES or ''),
            'extras_require': {
                name: str(reqs) for name, reqs in self.EXTRAS.items()},
            # always provide empty default collections
            # to make sure that any custom setup hooks
            # can always directly add stuff
            # even if no data defined in zetup config
            'packages': [],
            'package_dir': {},
            'package_data': {},
            'py_modules': self.MODULES or [],
            'entry_points': {},
            'classifiers': self.CLASSIFIERS or [],
            'keywords': self.KEYWORDS or [],
        }
        if self.EXTRAS:
            keywords['extras_require']['all'] = str(self.EXTRAS['all'])
        if self.VERSION:
            keywords['version'] = str(self.VERSION)
        if self.PACKAGES:
            namespaces = set()
            for pkg in self.PACKAGES:
                main = pkg.split('.')[0]
                if not os.path.exists(os.path.join(main, '__init__.py')):
                    namespaces.add(main)
            if namespaces:
                keywords['namespace_packages'] = list(namespaces)
            keywords['packages'] = list(map(str, self.PACKAGES))
            for pkg in self.PACKAGES:
                if pkg._path:
                    keywords['package_dir'][str(pkg)] = str(pkg._path)
        if self.ZETUP_CONFIG_PACKAGE:
            keywords['package_dir'][self.ZETUP_CONFIG_PACKAGE] = '.'
            keywords['package_data'][self.ZETUP_CONFIG_PACKAGE] \
              = self.ZETUP_DATA
        if self.SCRIPTS:
            entry_points = keywords['entry_points'].setdefault(
                'console_scripts', [])
            for name, source in self.SCRIPTS.items():
                entry_points.append('%s = %s' % (name, source))
        if self.SETUP_KEYWORDS:
            entry_points = keywords['entry_points'].setdefault(
                'distutils.setup_keywords', [])
            for name, source in self.SETUP_KEYWORDS.items():
                entry_points.append('%s = %s' % (name, source))
        cmdclasses = {}
        for cmdname in self.COMMANDS:
            cmdmethod = getattr(self, cmdname)

            class ZetupCommand(Command):
                # Must override options handling stuff from Command base...
                user_options = []

                def initialize_options(self):
                    pass

                def finalize_options(self):
                    pass

                run = staticmethod(cmdmethod)

            ZetupCommand.__name__ = cmdname
            cmdclasses[cmdname] = ZetupCommand

        keywords['cmdclass'] = cmdclasses
        return keywords

    @property
    def setup(self):
        return Setup(zfg=self)

    def __call__(self, subprocess=False, **setup_keywords):
        """Run `setup()` with generated keywords from zetup config
           and custom override `setup_keywords`.

        - If `subprocess` is True, run the dynamically generated setup.py
          (if zetup's extra 'commands' requirements are installed)
          with parameters from sys.argv in an external python process
          instead of directly calling setuptools.setup()
        """
        return self.setup(subprocess=subprocess, **setup_keywords)

    COMMANDS = []

    @classmethod
    def command(cls, name=None, args=None, depends=None):
        return CommandDeco(cls, name, args, depends)

    def __repr__(self):
        """Show class name, dist name, and project path.
        """
        return "<%s: %s (%s)>" % (
            type(self).__name__, self.NAME, self.ZETUP_DIR)


class Setup(dict):
    def __init__(self, zfg):
        dict.__init__(self, zfg.setup_keywords())
        self.zfg = zfg

    def __call__(self, subprocess=False, **keywords):
        """Run ``setup()`` with generated keywords from zetup config
           and custom override `keywords`.

        - If `subprocess` is True, run ``python setup.py`` with ``sys.argv``
          (see :meth:`Zetup.__call__` for details)
        """
        keywords = dict(self, **keywords)
        if 'make' in Zetup.COMMANDS:
            make_targets = ['VERSION', 'setup.py', 'zetup_config']
            with self.zfg.make(targets=make_targets):
                if subprocess:
                    return call([sys.executable, 'setup.py']
                                + sys.argv[1:])

                dist = setup(**keywords)
        else:
            dist = setup(**keywords)
        # to be always able to del dist.zetup_made in setup.py
        dist.zetup_made = None
        return dist


class CommandDeco(object):
    def __init__(self, zetupcls, name=None, args=None, depends=None):
        self.zetupcls = zetupcls
        self.name = name
        self.args = args
        self.make_targets = depends and list(depends)

    def __call__(self, func):
        """Add a command function as method to :class:`zetup.Zetup`
           and store its name in `cls.COMMANDS`.

        - Used in ``zetup.commands.*`` to sparate command implementations.
        """
        targets = self.make_targets

        def cmdmethod(zfg, args=None, **kwargs):
            if not targets:
                return func(zfg, args, **kwargs)
            from zetup.commands.make import make
            with make(zfg, targets=targets):
                return func(zfg, args, **kwargs)

        name = cmdmethod.__name__ = self.name or func.__name__
        cmdmethod.args = self.args

        setattr(self.zetupcls, name, cmdmethod)
        self.zetupcls.COMMANDS.append(name)
        return cmdmethod


def find_zetup_config(pkgname):
    zfg_modname = pkgname + '.zetup_config'
    try: # Already imported?
        return sys.modules[zfg_modname]
    except KeyError:
        pass
    try:
        return import_module(zfg_modname)
    except ImportError:
        pass
    # ==> no zetup config module
    # ==> assume package imported from source (repo)
    # ==> load setup config from package's parent path:
    mod = sys.modules[pkgname]
    path = os.path.dirname(os.path.dirname(os.path.realpath(mod.__file__)))
    for _ in range(pkgname.count('.')):
        # move further up the dir tree for every prefix (namespace) package
        path = os.path.dirname(path)
    try:
        return Zetup(path)
    except ZetupConfigNotFound as e:
        raise ZetupConfigNotFound(
            "No '%s.zetup_config' module and: %s" % (pkgname, e))
