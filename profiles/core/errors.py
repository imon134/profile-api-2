"""
Centralized error handling with consistent response format.
All API errors follow a standardized JSON envelope.
Enterprise-grade error management.
"""

from django.http import JsonResponse
from typing import Optional


class APIError(Exception):
    """
    Base class for all API errors.
    Provides consistent error structure across the application.
    """

    def __init__(self, message: str, status_code: int = 500):
        """
        Initialize API error.

        Args:
            message: Error message
            status_code: HTTP status code
        """
        self.message = message
        self.status_code = status_code
        super().__init__(message)

    def to_response(self) -> JsonResponse:
        """
        Convert error to JSON response.

        Returns:
            JsonResponse with error envelope
        """
        return JsonResponse(
            {
                "status": "error",
                "message": self.message,
            },
            status=self.status_code,
        )


class ValidationError(APIError):
    """Raised when request validation fails (400 Bad Request)"""

    def __init__(self, message: str):
        super().__init__(message, 400)


class PaginationError(APIError):
    """Raised when pagination parameters are invalid (400 Bad Request)"""

    def __init__(self, message: str):
        super().__init__(message, 400)


class NotFoundError(APIError):
    """Raised when resource not found (404 Not Found)"""

    def __init__(self, message: str = "Resource not found"):
        super().__init__(message, 404)


class ParseError(APIError):
    """Raised when query cannot be interpreted (400 Bad Request)"""

    def __init__(self, message: str = "Unable to interpret query"):
        super().__init__(message, 400)


class ServerError(APIError):
    """Raised for internal server errors (500 Internal Server Error)"""

    def __init__(self, message: str = "Internal server error"):
        super().__init__(message, 500)


def error_response(message: str, status_code: int = 500) -> JsonResponse:
    """
    Create consistent error response.

    Args:
        message: Error message
        status_code: HTTP status code

    Returns:
        JsonResponse with error envelope
    """
    return JsonResponse(
        {
            "status": "error",
            "message": message,
        },
        status=status_code,
    )


def success_response(
    data: list,
    page: int,
    limit: int,
    total: int,
) -> JsonResponse:
    """
    Create consistent success response.

    Args:
        data: List of serialized objects
        page: Current page number
        limit: Items per page
        total: Total count

    Returns:
        JsonResponse with success envelope
    """
    return JsonResponse(
        {
            "status": "success",
            "page": page,
            "limit": limit,
            "total": total,
            "data": data,
        },
        status=200,
    )
