class AidaException(Exception):
    pass


class AidaInternalException(AidaException):
    pass


class AidaExternalException(AidaException):
    pass


class AidaIoException(AidaExternalException):
    pass
