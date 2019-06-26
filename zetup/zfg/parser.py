"""The parsing framework for ZFG files."""

from __future__ import absolute_import

import re

from six import reraise

from zetup.error import ZetupError
from zetup.object import object, meta

from .data import ZFGData
from .line import BlankLine, OptionLine, SectionLine

__all___ = (
    'ZFG_PARSER', 'ZFGData', 'ZFGParser', 'ZFGSyntaxError', 'parse_zfg')


class ZFGSyntaxError(ZetupError):
    """A ZFG file dosen't follow common INI file syntax."""

    pass


class ZFGParser(object):
    """
    The ZFG file parser.

    ZFG files are actually syntax-compatible with INI files, but their parser
    provides convenient semantic and user-style-friendly extensions, some of
    which are often found in ``.ini`` file handling implementations:

    -   Implicit hierarchies separated by colons in the section names
    -   Sections are partial. Their content can be extended in multiple
        appearances
    -   The resulting parser data stores the exact input file style, including
        original section and option order and even any kind of unnecessary
        white-space, and this is preserved as much as possible when altering
        the data and regenrating text from it

    There is a pre-initialized :const:`zetup.ZFG_PARSER` instance, and its
    :meth:`zetup.ZFGParser.parse` is exposed as :const:`parse_zfg`

    >>> zfgtext = '''
    ... [main]
    ... option = value
    ...
    ... [other]
    ... other option =other value
    ...
    ... [main:sub]
    ... sub option =  sub value
    ... other sub option= other sub value
    ...
    ...
    ... [main]
    ...
    ... further option =   further value
    ... '''.lstrip()

    >>> from zetup import parse_zfg
    >>> zfg = parse_zfg(zfgtext)

    >>> zfg.sections()
    ['main', 'other']

    >>> zfg['main'].options()
    ['option', 'further option']

    >>> zfg['other'].options()
    ['other option']

    >>> zfg['main'].subsections()
    ['sub']

    >>> zfg['main']['sub'].options()
    ['sub option', 'other sub option']
    """

    lineno = None
    match = None
    stack = None

    def parse(self, text, zfg=None):
        if zfg is None:
            zfg = ZFGData()

        def parse_lines():
            if self.lineno > len(text_lines):
                return

            line = text_lines[self.lineno - 1]
            for pattern, handlercls in ZFG_PARSER_RULES:
                match = re.match(pattern, line)
                if match:
                    self.match = match
                    handlercls(parser=self)

                    self.lineno += 1
                    parse_lines()
                    break

            else:
                raise ZFGSyntaxError(self.lineno)

        zfg._lines = []
        self.stack = [zfg]
        self.lineno = 1
        text_lines = text.split('\n')
        parse_lines()
        return zfg


#: The pre-defined :class:`zetup.ZFGParser` instance.
ZFG_PARSER = ZFGParser()


#: The pre-defined function for parsing ZFG files.
#
#  See :class:`zetup.ZFGParser` for more information about ``.zfg`` files
parse_zfg = ZFG_PARSER.parse


#: The regexes and according handlers for parsing ZFG file lines.
#
#  Internally used by :class:`zetup.ZFGParser`
ZFG_PARSER_RULES = [
    (
        r'^\s*$',
        BlankLine),
    (
        r'^\[(?P<name>[^\[\]]+)\]\s*$',
        SectionLine),
    (
        r'^(?P<name>[^\s=][^=]*[^\s=])\s*=\s*(?P<value>.*\S)\s*$',
        OptionLine),
    (
        r'^(?P<name>[^\s=][^=]*[^\s=])\s*=\s*$',
        OptionLine),
]
