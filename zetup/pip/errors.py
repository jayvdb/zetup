"""Define exceptions for failing ``zetup.pip`` calls."""

from zetup.error import ZetupError


class ZetupPipError(ZetupError):
    """
    ``zetup.pip([command...])`` failed.
    
    ``.command`` argument list and ``.exit_code`` can be retrieved from the
    exception object:

    >>> import zetup

    >>> try:
    ...     zetup.pip(['invalid'])
    ... except zetup.ZetupPipError as exc:
    ...     exc.command, exc.exit_code
    (['invalid'], 1)
    """

    def __init__(self, command, exit_code):
        """
        Compose error message from `command` list and `exit_code`.

        Also store the parameters as exception object attributes
        """
        ZetupError.__init__(
            self, "pip command {!r} failed with exit code {:d}".format(
                command, exit_code))
        self.command = command
        self.exit_code = exit_code
