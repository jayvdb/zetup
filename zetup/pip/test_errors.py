"""Test :mod:`zetup.pip.errors`."""

import zetup
from zetup.pip.errors import ZetupPipError


class TestZetupPipError:
    """Test :exc:`zetup.pip.errors.ZetupPipError`."""

    def test_toplevel_export(self):
        """Should be properly provided by :mod:`zetup` API."""
        assert zetup.ZetupPipError is ZetupPipError

    def test_superclass(self):
        """Should be derived from :exc:`zetup.ZetupError`."""
        assert issubclass(ZetupPipError, zetup.ZetupError)

    def test_attributes(self):
        """Should store ``.command`` and ``.exit_code``."""
        exc = ZetupPipError(['invalid'], 1)
        assert exc.command == ['invalid']
        assert exc.exit_code is 1

    def test_message(self):
        """Should provide correct exception message."""
        exc = ZetupPipError(['invalid'], 1)
        assert str(exc) == "pip command ['invalid'] failed with exit code 1"
