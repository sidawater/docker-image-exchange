"""
Message service exception definitions

Defines exception types that the client may encounter.
"""


class MessageServiceError(Exception):
    """Message service base exception"""
    pass


class ValidationError(MessageServiceError):
    """Validation error exception"""
    pass


class NotFoundError(MessageServiceError):
    """Resource not found exception"""
    pass


class AuthenticationError(MessageServiceError):
    """Authentication error exception"""
    pass


class ServerError(MessageServiceError):
    """Server error exception"""
    pass
