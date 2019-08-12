from __future__ import print_function

import sys
import os

# from setuptools import Distribution
from pkg_resources import get_distribution, working_set, VersionConflict


def samefile(path, other):
    """
    Workaround for missing ``os.path.samefile`` in Windows Python 2.7.
    """
    return os.path.normcase(os.path.normpath(os.path.realpath(path))) \
        == os.path.normcase(os.path.normpath(os.path.realpath(other)))


sys.path.insert(0, os.path.dirname(os.path.realpath(__file__)))
try:
    import zetup
except VersionConflict:
    egg_info = 'zetup.egg-info'
    dist = get_distribution('zetup')
    if samefile(
            dist.location, os.path.dirname(os.path.realpath(__file__))
    ) and os.path.exists(egg_info):
        print("zetup: Removing possibly outdated %s/" % egg_info,
              # don't pollute stdout
              file=sys.stderr)
        for fname in os.listdir(egg_info):
            os.remove(os.path.join(egg_info, fname))
        os.rmdir(egg_info)
        # when run via pip, the egg-info is still referenced by setuptools,
        # which would try to read the contents
        for keys in working_set.entry_keys.values():
            if 'zetup' in keys:
                keys.remove('zetup')
        del working_set.by_key['zetup']


from zetup import Zetup, DistributionNotFound, VersionConflict
try:
    from zetup.commands import make, pytest, tox, conda
except (ImportError, DistributionNotFound, VersionConflict):
    # ==> no zetup commands available
    # standard setup commands work anyway
    pass


# setup_req = 'setuptools >= 15.0'
# try:
#     get_distribution(setup_req)
# except VersionConflict:
#     for mod in ['setuptools', 'pkg_resources']:
#         for name, _ in list(sys.modules.items()):
#             if name == mod or name.startswith(mod + '.'):
#                 del sys.modules[name]
#     sys.path.insert(0, Distribution().fetch_build_egg(setup_req))


zfg = Zetup()
zetup.requires.Requirements('setuptools >= 39.1', zfg=zfg).check()

setup = zfg.setup
setup['package_data']['zetup.commands.make'] = [
    'templates/*.jinja',
    'templates/package/*.jinja',
]
setup()
