"""
Request parameter validation and type conversion.
Centralized validation reduces code duplication and improves maintainability.
Enterprise-grade validation with type hints and comprehensive error messages.
"""

from typing import Optional, Any
import re
from profiles.core.errors import ValidationError
from profiles.core.constants import FilterConstants


def to_int(value: Any, field_name: str = "value") -> Optional[int]:
    """
    Safe conversion of value to integer.

    Args:
        value: Value to convert
        field_name: Name of field for error message

    Returns:
        Integer value or None if input is None

    Raises:
        ValidationError: If value cannot be converted to int
    """
    if value is None or value == "":
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        raise ValidationError(f"{field_name} must be an integer, got '{value}'")


def to_float(value: Any, field_name: str = "value") -> Optional[float]:
    """
    Safe conversion of value to float.

    Args:
        value: Value to convert
        field_name: Name of field for error message

    Returns:
        Float value or None if input is None

    Raises:
        ValidationError: If value cannot be converted to float
    """
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        raise ValidationError(f"{field_name} must be a decimal number, got '{value}'")


class QueryValidator:
    """Validates query parameters for filtering endpoints"""

    @staticmethod
    def validate_gender(gender: Optional[str]) -> Optional[str]:
        """
        Validate and normalize gender parameter.

        Args:
            gender: Gender value ('male' or 'female')

        Returns:
            Lowercased gender or None if not provided

        Raises:
            ValidationError: If gender is invalid
        """
        if gender is None or gender == "":
            return None

        gender_lower = gender.lower()
        if gender_lower not in FilterConstants.GENDER_CHOICES:
            raise ValidationError(f"gender must be 'male' or 'female', got '{gender}'")

        return gender_lower

    @staticmethod
    def validate_age_group(age_group: Optional[str]) -> Optional[str]:
        """
        Validate and normalize age_group parameter.

        Args:
            age_group: Age group value

        Returns:
            Lowercased age_group or None if not provided

        Raises:
            ValidationError: If age_group is invalid
        """
        if age_group is None or age_group == "":
            return None

        age_group_lower = age_group.lower()
        if age_group_lower not in FilterConstants.AGE_GROUP_CHOICES:
            allowed = ", ".join(FilterConstants.AGE_GROUP_CHOICES)
            raise ValidationError(
                f"age_group must be one of: {allowed}, got '{age_group}'"
            )

        return age_group_lower

    @staticmethod
    def validate_country_id(country_id: Optional[str]) -> Optional[str]:
        """
        Validate country_id parameter.

        Args:
            country_id: ISO country code (2 characters)

        Returns:
            Uppercase country_id or None if not provided

        Raises:
            ValidationError: If country_id is invalid
        """
        if country_id is None or country_id == "":
            return None

        country_id_upper = country_id.upper()
        if len(country_id_upper) != 2 or not country_id_upper.isalpha():
            raise ValidationError(
                f"country_id must be a 2-letter ISO code, got '{country_id}'"
            )

        return country_id_upper

    @staticmethod
    def validate_min_age(min_age: Optional[int]) -> Optional[int]:
        """
        Validate minimum age parameter.

        Args:
            min_age: Minimum age value

        Returns:
            Validated min_age or None

        Raises:
            ValidationError: If min_age is invalid
        """
        if min_age is None:
            return None

        if not isinstance(min_age, int):
            raise ValidationError("min_age must be an integer")

        FilterConstants.validate_age(min_age, "min_age")
        return min_age

    @staticmethod
    def validate_max_age(max_age: Optional[int]) -> Optional[int]:
        """
        Validate maximum age parameter.

        Args:
            max_age: Maximum age value

        Returns:
            Validated max_age or None

        Raises:
            ValidationError: If max_age is invalid
        """
        if max_age is None:
            return None

        if not isinstance(max_age, int):
            raise ValidationError("max_age must be an integer")

        FilterConstants.validate_age(max_age, "max_age")
        return max_age

    @staticmethod
    def validate_gender_probability(prob: Optional[float]) -> Optional[float]:
        """
        Validate gender probability parameter.

        Args:
            prob: Probability value

        Returns:
            Validated probability or None

        Raises:
            ValidationError: If probability is invalid
        """
        if prob is None:
            return None

        if not isinstance(prob, float):
            raise ValidationError("gender_probability must be a decimal number")

        FilterConstants.validate_probability(prob, "gender_probability")
        return prob

    @staticmethod
    def validate_country_probability(prob: Optional[float]) -> Optional[float]:
        """
        Validate country probability parameter.

        Args:
            prob: Probability value

        Returns:
            Validated probability or None

        Raises:
            ValidationError: If probability is invalid
        """
        if prob is None:
            return None

        if not isinstance(prob, float):
            raise ValidationError("country_probability must be a decimal number")

        FilterConstants.validate_probability(prob, "country_probability")
        return prob

    @staticmethod
    def validate_sort_by(sort_by: str) -> str:
        """
        Validate sort_by parameter.

        Args:
            sort_by: Field to sort by

        Returns:
            Validated sort_by value

        Raises:
            ValidationError: If sort_by is invalid
        """
        if not sort_by or sort_by == "":
            return FilterConstants.DEFAULT_SORT_BY

        try:
            FilterConstants.validate_sort_by(sort_by)
        except ValueError as e:
            raise ValidationError(str(e))

        return sort_by

    @staticmethod
    def validate_order(order: str) -> str:
        """
        Validate order parameter.

        Args:
            order: Sort order ('asc' or 'desc')

        Returns:
            Validated order value

        Raises:
            ValidationError: If order is invalid
        """
        if not order or order == "":
            return FilterConstants.DEFAULT_ORDER

        order_lower = order.lower()
        try:
            FilterConstants.validate_order(order_lower)
        except ValueError as e:
            raise ValidationError(str(e))

        return order_lower


class SearchValidator:
    """Validates natural language search queries"""

    MAX_QUERY_LENGTH = 500
    ALLOWED_PATTERN = re.compile(r"^[a-z0-9\s\-]+$", re.IGNORECASE)

    @staticmethod
    def validate_search_query(q: Optional[str]) -> str:
        """
        Validate search query with sanitization.

        Args:
            q: Search query string

        Returns:
            Sanitized query

        Raises:
            ValidationError: If query is invalid
        """
        if not q or not q.strip():
            raise ValidationError("Search query cannot be empty")

        q = q.strip().lower()

        # Length check
        if len(q) > SearchValidator.MAX_QUERY_LENGTH:
            raise ValidationError(
                f"Search query too long (max {SearchValidator.MAX_QUERY_LENGTH} characters)"
            )

        # Pattern check: only alphanumeric, spaces, hyphens
        if not SearchValidator.ALLOWED_PATTERN.match(q):
            raise ValidationError(
                "Search query contains invalid characters. "
                "Use only letters, numbers, spaces, and hyphens."
            )

        return q