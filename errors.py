class AppError(Exception):
    code = "unknown"


class DomainDataError(AppError):
    code = "domain error"


class InvalidStateError(AppError):
    code = "state error"


class MissingNowError(DomainDataError):
    code = "missing now"


class OperationAborted(Exception):
    pass
