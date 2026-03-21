class CreditSystemException(Exception):
    """Base exception for the credit system."""
    def __init__(self, message: str = "Something went wrong during credit operations") -> None:
        super().__init__(message)
        self.message = message


class UserNotFoundError(CreditSystemException):
    """Raised when a user with the specified ID does not exist."""
    def __init__(self, user_id: int) -> None:
        super().__init__(f"There is no user with id={user_id}")


class CreditNotFoundError(CreditSystemException):
    """Raised when a credit with the specified ID is not found."""
    def __init__(self, credit_id: int) -> None:
        super().__init__(f"Credit with id={credit_id} not found")


class PlanValidationError(CreditSystemException):
    """Raised when a plan fails validation."""
    def __init__(self, message: str = "Plan validation failed") -> None:
        super().__init__(message)


class NoPlansFoundError(CreditSystemException):
    """Raised when no plans are found in the database."""
    def __init__(self, message: str = "No plans found in the database") -> None:
        super().__init__(message)


class CreditDataInconsistencyError(CreditSystemException):
    """Raised when credit data is inconsistent or corrupted."""
    def __init__(self, message: str = "Credit data is inconsistent or corrupted") -> None:
        super().__init__(message)
