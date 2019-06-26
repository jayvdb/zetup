"""Handlers for parsed ZFG text lines."""

__all__ = ('BlankLine', 'SectionLine', 'OptionLine')


class Line(object):
    """The basic ZFG text line handler."""

    #: The optional identification name of the parsed ZFG file line.
    name = None

    def __init__(self, parser):
        """
        Initialize with :class:`zetup.ZFGParser` instance.

        To get current line number, line text, line regex match object,
        and to access the parser stack
        """
        self.lineno = parser.lineno
        self.text = parser.match.group().rstrip('\r\n')
        parser.stack[-1].lines.append(self)

    def to_zfg(self):
        """Re-create ZFG line text."""
        return self.text

    def __repr__(self):
        """Show line type, line number, and original line text."""
        cls = type(self)
        return "<{} from line {}: {!r}>".format(
            self.name and "{} {!r}".format(cls, self.name) or cls,
            self.lineno, self.text)

Line.__package__ = __package__


class BlankLine(Line):
    """A parsed blank ZFG text line."""

    def __init__(self, parser):
        """Ensure that the line is really blank."""
        super(BlankLine, self).__init__(parser)
        assert not self.text.strip(), (
            "Internal ZFGParser error! Line {} is not really blank: {!r}"
            .format(self.lineno, self.text))


class BlockHeaderLine(Line):
    """
    Base class for parsed ZFG text lines starting data blocks.

    Like sections and options with multi-line values
    """

    #: The parsed sub-lines of a ZFG file's block header line.
    lines = None

    def __init__(self, parser):
        """Initialize the list of the block's sub-lines."""
        super(BlockHeaderLine, self).__init__(parser)
        self.lines = []

    def to_zfg(self):
        """Re-create ZFG data block text."""
        zfg = super(BlockHeaderLine, self).to_zfg()
        if self.lines:
            zfg += "\n{}".format("\n".join(
                line.to_zfg() for line in self.lines))
        return zfg


class SectionLine(BlockHeaderLine):
    """A parsed section header line of ZFG text."""

    def __init__(self, parser):
        """Extract section name and add line handler to the parser stack."""
        if isinstance(parser.stack[-1], OptionLine):
            # remove option header line from parser stack
            optline = parser.stack.pop(-1)
            super_line = parser.stack[-1]
            assert isinstance(super_line, SectionLine), (
                "Interal ZFGParser error! Below {!r} should be a "
                "SectionLine on a the stack, but found {!r}"
                .format(optline, super_line))

        from .data import ZFGData  # avoid circular import
        if isinstance(parser.stack[-1], SectionLine):
            # remove previous section header line from parser stack
            old_line = parser.stack.pop(-1)
            super_line = parser.stack[-1]
            assert isinstance(super_line, ZFGData), (
                "Interal ZFGParser error! Below {!r} should be a ZFGData "
                "object on a the stack, but found {!r}"
                .format(old_line, super_line))

        super(SectionLine, self).__init__(parser)
        self.name = parser.match.group('name')
        parser.stack.append(self)


class OptionLine(BlockHeaderLine):
    """A parsed option header or ``option = value`` line of ZFG text."""

    #: The optional inline value of the ZFG file's option line.
    value = None

    def __init__(self, parser):
        """
        Extract option name and optionally inline option value.

        And add line handler to the parser stack in the non-inline case
        """
        super(OptionLine, self).__init__(parser)
        groups = parser.match.groupdict()
        self.name = groups['name']
        if 'value' in groups:  # ==> inline option value
            self.value = parser.match.group('value')

        else:
            if isinstance(parser.stack[-1], OptionLine):
                # remove previous option header line from parser stack
                old_line = parser.stack.pop(-1)
                super_line = parser.stack[-1]
                assert isinstance(super_line, SectionLine), (
                    "Interal ZFGParser error! Below {!r} should be a "
                    "SectionLine on a the stack, but found {!r}"
                    .format(old_line, super_line))

            parser.stack[-1].lines.append(self)
            parser.stack.append(self)

    def __repr__(self):
        if self.value:
            return "<{} {!r} with value {!r} from line {}: {!r}>".format(
                type(self).__name__, self.name, self.value,
                self.lineno, self.text)

        return super(OptionLine, self).__repr__()
