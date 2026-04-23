"""
Pagination utilities with proper error handling.
Uses exception-based error handling for clean separation of concerns.
"""

from typing import Tuple, Dict, Any, Union
from django.db.models import QuerySet
from profiles.core.errors import PaginationError
from profiles.core.constants import FilterConstants


def paginate(
    qs: QuerySet,
    page: Union[int, str],
    limit: Union[int, str],
) -> Tuple[QuerySet, Dict[str, Any]]:
    """
    Paginate a queryset with validation.

    Handles pagination of query results with automatic limit capping.

    Args:
        qs: Django QuerySet to paginate
        page: Page number (1-indexed, string or int)
        limit: Items per page (string or int)

    Returns:
        Tuple of (sliced_queryset, metadata_dict) where metadata contains:
        - page: Page number
        - limit: Items per page (capped at MAX_LIMIT)
        - total: Total count of records

    Raises:
        PaginationError: If page or limit are invalid

    Example:
        >>> qs = Profile.objects.all()
        >>> result, meta = paginate(qs, 1, 10)
        >>> len(result) # Returns up to 10 items
        >>> meta['total'] # Total records in queryset
    """
    # Convert to integers
    try:
        page = int(page)
        limit = int(limit)
    except (TypeError, ValueError):
        raise PaginationError("page and limit must be integers")

    # Validate page
    if page < FilterConstants.MIN_PAGE:
        raise PaginationError(f"page must be >= {FilterConstants.MIN_PAGE}")

    # Validate limit
    if limit < FilterConstants.MIN_LIMIT:
        raise PaginationError(f"limit must be >= {FilterConstants.MIN_LIMIT}")

    # Cap limit at maximum
    if limit > FilterConstants.MAX_LIMIT:
        limit = FilterConstants.MAX_LIMIT

    # Calculate pagination
    total = qs.count()
    start = (page - 1) * limit
    end = start + limit

    return qs[start:end], {
        "page": page,
        "limit": limit,
        "total": total,
    }