from .strings.error import *


class Error(Exception):
    pass


class InvalidNArgsError(Error):
    def __init__(self, cmd: str, n_args_expected: int, n_args: int):
        super().__init__(INVALID_NARGS_ERROR.format(cmd, n_args_expected,
                                                    n_args))


class NotFoundError(Error):
    pass


class AlreadyFoundError(Error):
    pass
