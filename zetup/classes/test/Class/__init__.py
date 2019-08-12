"""A sample :class:`zetup.class_package` for testing purposes."""

import zetup

zetup.class_package(__name__, member_modules=['methods'])


class Class(zetup.object):

    def __init__(self):
        pass
