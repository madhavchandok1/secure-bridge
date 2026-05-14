class NotFoundError(Exception):
    """
    Raised when a resource is not found.
    """


class ForbiddenError(Exception):
    """
    Raised when access is forbidden.
    """


class UnauthorizedError(Exception):
    """
    Raised when authentication fails.
    """


class ConflictError(Exception):
    """
    Raised when conflicting data exists.
    """


class ValidationError(Exception):
    """
    Raised for validation-related failures.
    """