# zetup.py
#
# Zimmermann's Python package setup.
#
# Copyright (C) 2014 Stefan Zimmermann <zimmermann.code@gmail.com>
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

import sys
import os

try:
    from setuptools import setup, Command
except ImportError: # fallback
    # (setuptools should at least be available after package installation)
    from distutils.core import setup, Command

from .config import load_zetup_config


class Zetup(object):
    def __init__(self, ZETUP_DIR='.'):
        """Load and store zetup config from `ZETUP_DIR`
           as attributes in `self`.
        """
        load_zetup_config(ZETUP_DIR, cfg=self)

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
          'install_requires': str(self.REQUIRES),
          'extras_require':
            {name: str(reqs) for name, reqs in self.EXTRAS.items()},
          'classifiers': self.CLASSIFIERS,
          'keywords': self.KEYWORDS,
          }
        if self.VERSION:
          keywords['version'] = str(self.VERSION)
        if self.PACKAGES:
            keywords['packages'] = self.PACKAGES
        if self.ZETUP_CONFIG_PACKAGE:
            keywords.update({
              'package_dir': {self.ZETUP_CONFIG_PACKAGE: '.'},
              'package_data': {self.ZETUP_CONFIG_PACKAGE: self.ZETUP_DATA},
              })
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

    def __call__(self, **setup_keywords):
        """Run `setup()` with generated keywords from zetup config
           and custom override `setup_keywords`.
        """
        keywords = self.setup_keywords()
        keywords.update(setup_keywords)
        return setup(**keywords)

    COMMANDS = []

    @classmethod
    def command(cls, func):
        """Add a command function as method to :class:`Zetup`
           and store its name in `cls.COMMANDS`.

        - Used in `zetup.commands.*` to sparate command implementations.
        """
        name = func.__name__
        setattr(cls, name, func)
        cls.COMMANDS.append(name)


# If installed with pip, add all build directories and src/ subdirs
#  of implicitly downloaded requirements
#  to sys.path and os.environ['PYTHONPATH']
#  to make them importable during installation:
sysbuildpath = os.path.join(sys.prefix, 'build')
try:
    fnames = os.listdir(sysbuildpath)
except OSError:
    pass
else:
    if 'pip-delete-this-directory.txt' in fnames:
        pkgpaths = []
        for fn in fnames:
            path = os.path.join(sysbuildpath, fn)
            if not os.path.isdir(path):
                continue
            path = os.path.abspath(path)
            pkgpaths.append(path)

            srcpath = os.path.join(path, 'src')
            if os.path.isdir(srcpath):
                pkgpaths.append(srcpath)

        for path in pkgpaths:
            sys.path.insert(0, path)

        PYTHONPATH = os.environ.get('PYTHONPATH')
        PATH = ':'.join(pkgpaths)
        if PYTHONPATH is None:
            os.environ['PYTHONPATH'] = PATH
        else:
            os.environ['PYTHONPATH'] = ':'.join([PATH, PYTHONPATH])


# If this is a locally imported zetup.py in zetup's own repo...
# if (NAME == 'zetup' #==> is in zetup's own package/repo
#     and os.path.basename(__file__).startswith('zetup')
#     #"=> was not exec()'d from setup.py
#     and not 'zetup.zetup' in sys.modules
#     #"=> was not imported as subpackage
#     ):
#     #... then fake the interface of the installed zetup package...
#     import zetup # import itself as faked subpackage

#     ## __path__ = [os.path.join(ZETUP_DIR, 'zetup')]
#     __path__ = [ZETUP_DIR]
#     # Exec the __init__ which gets installed in top level zetup package:
#     exec(open('__init__.py').read().replace('from . import zetup', ''))
