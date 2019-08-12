"""High-level ZFG file handling."""

from .data import ZFGData
from .parser import parse_zfg

__all__ = ('ZFGFile', )


class ZFGFile(ZFGData):
    """
    The actual ZFG file handler.

    >>> from zetup import ZFGFile

    >>> import os
    >>> zfg = ZFGFile(os.path.join(os.path.dirname(__file__), 'test.zfg'))
    >>> zfg
    ZFGFile '...test.zfg'
    >>> zfg.path
    '...test.zfg'

    Parse the file text on :meth:`.load`, which can then be accessed and
    changed via the basic :class:`zetup.ZFGData` API:

    >>> zfg.load()
    >>> zfg.sections()
    ['test section', 'other test section']

    Save back changed data with :meth:`.save`, which preserves the original
    user-style of the input text as much as possible
    """

    def __init__(self, path):
        """Initialize with a ZFG file `path`."""
        super(ZFGFile, self).__init__()
        self.path = path

    def load(self):
        """Parse the ZFG file text."""
        with open(self.path) as file:
            parse_zfg(file.read(), zfg=self)

    def save(self):
        """Save data back to the ZFG file."""
        with open(self.path, 'w') as file:
            file.write(str(self))

    def __repr__(self):
        """Show ZFG file path and loaded content."""
        text = "{} {!r}".format(type(self).__name__, self.path)
        if self.lines:
            text += "\n{}".format(super(ZFGFile, self).__repr__())
        return text
