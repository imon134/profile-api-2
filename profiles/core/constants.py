"""
Query parameters and parsing configuration.
This is the single source of truth for all query validation and business logic.
Enterprise-grade configuration management.
"""

from typing import Dict, Tuple


class FilterConstants:
    """Allowed filter fields and their configurations"""

    # Gender field definitions
    GENDER_CHOICES = ("male", "female")
    GENDER_HELP = "Filter by gender: 'male' or 'female'"

    # Age group definitions
    AGE_GROUP_CHOICES = ("child", "teenager", "adult", "senior")
    AGE_GROUP_HELP = "Filter by age group: child, teenager, adult, senior"

    # Sorting configuration
    ALLOWED_SORT_FIELDS = ["age", "created_at", "gender_probability"]
    ALLOWED_ORDERS = ["asc", "desc"]
    DEFAULT_SORT_BY = "created_at"
    DEFAULT_ORDER = "asc"
    SORT_BY_HELP = "Sort by: age, created_at, or gender_probability"
    ORDER_HELP = "Sort order: asc or desc"

    # Pagination configuration
    DEFAULT_PAGE = 1
    DEFAULT_LIMIT = 10
    MAX_LIMIT = 50
    MIN_PAGE = 1
    MIN_LIMIT = 1
    PAGE_HELP = "Page number (default: 1)"
    LIMIT_HELP = "Items per page (default: 10, max: 50)"

    # Probability thresholds
    MIN_PROBABILITY = 0.0
    MAX_PROBABILITY = 1.0

    # Age validation
    MIN_AGE = 0
    MAX_AGE = 150

    # Natural language parsing configuration
    COUNTRY_MAPPING: Dict[str, str] = {
        "nigeria": "NG",
        "kenyan": "KE",
        "kenya": "KE",
        "ghanaian": "GH",
        "ghana": "GH",
        "uganda": "UG",
        "tanzanian": "TZ",
        "tanzania": "TZ",
        "angolan": "AO",
        "angola": "AO",
        "benin": "BJ",
        "beninese": "BJ",
    }

    AGE_GROUP_MAPPING: Dict[str, str] = {
        "child": "child",
        "children": "child",
        "kid": "child",
        "kids": "child",
        "teenager": "teenager",
        "teenagers": "teenager",
        "teen": "teenager",
        "teens": "teenager",
        "adolescent": "teenager",
        "adult": "adult",
        "adults": "adult",
        "senior": "senior",
        "seniors": "senior",
        "elderly": "senior",
        "old": "senior",
    }

    # Age ranges for natural language parsing
    AGE_RANGES: Dict[str, Tuple[int, int]] = {
        "young": (16, 24),
        "youngster": (16, 24),
        "youth": (16, 24),
        "middle-aged": (35, 55),
        "old": (65, 100),
        "teenager": (13, 19),
    }

    @staticmethod
    def validate_sort_by(sort_by: str) -> None:
        """
        Validate sort_by parameter.

        Args:
            sort_by: Field to sort by

        Raises:
            ValueError: If sort_by is invalid
        """
        if sort_by not in FilterConstants.ALLOWED_SORT_FIELDS:
            allowed = ", ".join(FilterConstants.ALLOWED_SORT_FIELDS)
            raise ValueError(f"sort_by must be one of: {allowed}")

    @staticmethod
    def validate_order(order: str) -> None:
        """
        Validate order parameter.

        Args:
            order: Sort order

        Raises:
            ValueError: If order is invalid
        """
        if order not in FilterConstants.ALLOWED_ORDERS:
            raise ValueError("order must be 'asc' or 'desc'")

    @staticmethod
    def validate_gender(gender: str) -> None:
        """
        Validate gender parameter.

        Args:
            gender: Gender value

        Raises:
            ValueError: If gender is invalid
        """
        if gender.lower() not in FilterConstants.GENDER_CHOICES:
            raise ValueError("gender must be 'male' or 'female'")

    @staticmethod
    def validate_age_group(age_group: str) -> None:
        """
        Validate age_group parameter.

        Args:
            age_group: Age group value

        Raises:
            ValueError: If age_group is invalid
        """
        if age_group.lower() not in FilterConstants.AGE_GROUP_CHOICES:
            allowed = ", ".join(FilterConstants.AGE_GROUP_CHOICES)
            raise ValueError(f"age_group must be one of: {allowed}")

    @staticmethod
    def validate_probability(value: float, field_name: str) -> None:
        """
        Validate probability value.

        Args:
            value: Probability value
            field_name: Name of the field for error message

        Raises:
            ValueError: If probability is out of range
        """
        if not (FilterConstants.MIN_PROBABILITY <= value <= FilterConstants.MAX_PROBABILITY):
            raise ValueError(
                f"{field_name} must be between {FilterConstants.MIN_PROBABILITY} "
                f"and {FilterConstants.MAX_PROBABILITY}"
            )

    @staticmethod
    def validate_age(age: int, field_name: str = "age") -> None:
        """
        Validate age value.

        Args:
            age: Age value
            field_name: Name of the field for error message

        Raises:
            ValueError: If age is out of range
        """
        if not (FilterConstants.MIN_AGE <= age <= FilterConstants.MAX_AGE):
            raise ValueError(
                f"{field_name} must be between {FilterConstants.MIN_AGE} "
                f"and {FilterConstants.MAX_AGE}"
            )
