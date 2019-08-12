"""ZFG data structures."""

import json
from collections import OrderedDict

from zetup.object import object

from .line import OptionLine, SectionLine

__all__ = ('ZFGData', )


class ZFGEncoder(json.JSONEncoder):

    def default(self, obj):  # pylint: disable=method-hidden
        if isinstance(obj, ZFGSection):
            return OrderedDict(obj)

        super(ZFGEncoder, self).default(obj)


class ZFGData(object):
    """The basic manager class for parsed ZFG file data."""

    #: The parsed top-level lines of a ``.zfg`` file.
    lines = None

    def __init__(self):
        self.lines = []

    def __getitem__(self, key):
        if key not in self.sections():
            raise KeyError(key)

        return ZFGSection(key, data=self)

    def sections(self):
        """Get a list of all root-level sections."""
        result = []
        for parsed_line in self.lines:
            if isinstance(parsed_line, SectionLine):
                name = parsed_line.name.split(':')[0]
                if name not in result:
                    result.append(name)
        return result

    def to_zfg(self):
        return "\n".join(line.to_zfg() for line in self.lines)

    def __str__(self):
        return self.to_zfg()

    def __repr__(self):
        return "{}\n{}".format(type(self).__name__, json.dumps(
            OrderedDict((
                (name, OrderedDict(self[name]))
                for name in self.sections())),
            cls=ZFGEncoder, indent=4))


class ZFGSection(object):

    def __init__(self, name, data):
        self.name = name
        self.data = data

    def subsections(self):
        result = []
        for line in self.data.lines:
            if isinstance(line, SectionLine) and ':' in line.name:
                name, subname = line.name.split(':', 1)
                if name == self.name:
                    result.append(subname.split(':')[0])
        return result

    def options(self):
        result = []
        for line in self.data.lines:
            if isinstance(line, SectionLine):
                if line.name != self.name:
                    continue

                for line in line.lines:
                    if isinstance(line, OptionLine):
                        result.append(line.name)
        return result

    def __iter__(self):
        for line in self.data.lines:
            if isinstance(line, SectionLine):
                if line.name == self.name:
                    for line in line.lines:
                        if isinstance(line, OptionLine):
                            yield (line.name, line.value)

                elif ':' in line.name:
                    name, subname = line.name.rsplit(':', 1)
                    if name == self.name:
                        yield (subname, type(self)(line.name, self.data))

    def __getitem__(self, key):
        for name, data in self:
            if name == key:
                return data

        raise KeyError(key)

    def __repr__(self):
        return json.dumps(OrderedDict(self), indent=4)
