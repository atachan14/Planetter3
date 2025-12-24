class AppError(Exception):
    code = "unknown"

class DomainDataError(AppError):
    """ドメインデータが壊れているときの例外"""
    code = "domain error"
    pass

class InvalidStateError(AppError):
    code = "state error"
    pass