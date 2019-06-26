"""All about handling ZFG configuration files."""

from zetup.modules import package

from .data import ZFGData
from .file import ZFGFile
from .parser import ZFG_PARSER, ZFGParser, parse_zfg

package(__name__, (
    'ZFG_PARSER', 'ZFGData', 'ZFGFile', 'ZFGParser', 'parse_zfg'))
