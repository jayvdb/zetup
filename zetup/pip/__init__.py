"""Define :func:`zetup.pip` command runner and :exc:`zetup.ZetupPipError`."""

import logging

from zetup.requires import requires

from .errors import ZetupPipError

__all__ = ('ZetupPipError', 'pip')


@requires("pip >= 10.0")
def pip(command, raise_=True):
    """
    Run a pip `command`.

    :param command: The list of pip arguments

    >>> import zetup

    >>> zetup.pip(['list', '-v'])
    Package...Version...Location...Installer
    -------...-------...--------...---------
    ...
    0

    :return:
        ``0`` on success or, if called with ``raise_=False``, also any
        non-zero pip exit code

    >>> zetup.pip(['invalid'], raise_=False)
    1

    :raises zetup.ZetupPipError:
        on non-zero pip exit codes, if not called with ``raise_=False``

    >>> zetup.pip(['invalid'])
    Traceback (most recent call last):
    ...
    ZetupPipError: pip command ['invalid'] failed with exit code 1
    """
    from pip._internal import configuration, main

    # HACK: Avoid unnecessary debug messages (which also destroy doctests)
    configuration.logger.level = logging.INFO
    try:
        exit_code = main(command)
    except SystemExit as exc:
        exit_code = exc.code
    if raise_ and exit_code != 0:
        raise ZetupPipError(command, exit_code)

    return exit_code
