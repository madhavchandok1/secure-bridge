class AppError(Exception):
    """
    Base class for all application-specific exceptions.
    
    This acts as a parent for all custom errors, allowing you to catch 
    any 'known' application error in one block if needed.
    """
    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)


class NotFoundError(AppError):
    """
    Raised when a requested resource (e.g., User, Organization) does not exist.
    
    Mapping: Usually results in an HTTP 404 Not Found.
    """


class ForbiddenError(AppError):
    """
    Raised when the authenticated user lacks the necessary permissions.
    
    Mapping: Usually results in an HTTP 403 Forbidden.
    """


class UnauthorizedError(AppError):
    """
    Raised when authentication credentials are missing, invalid, or expired.
    
    Mapping: Usually results in an HTTP 401 Unauthorized.
    """


class ConflictError(AppError):
    """
    Raised when a request conflicts with the current state of the server.
    (e.g., trying to register a slug that is already taken).
    
    Mapping: Usually results in an HTTP 409 Conflict.
    """


class ValidationError(AppError):
    """
    Raised when the provided input fails business logic or schema validation.
    
    Mapping: Usually results in an HTTP 422 Unprocessable Entity.
    """