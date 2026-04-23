"""
Natural language search query parsing.
Converts plain English queries into database filters.
Rule-based parsing with no AI/LLM required.
"""

import re
from typing import Dict, Any
from profiles.core.constants import FilterConstants
from profiles.core.errors import ParseError


class SearchParser:
    """
    Parses natural language queries into database filters.

    Supported patterns:
    - Gender: "male", "female"
    - Age groups: "child", "teenager", "adult", "senior"
    - Age descriptors: "young" (16-24), "above 30", "above N"
    - Countries: "nigeria", "kenya", "ghana", etc.
    - Combined: "young males from nigeria", "female teenagers"
    """

    @staticmethod
    def parse(query: str) -> Dict[str, Any]:
        """
        Parse natural language query into filters.

        Args:
            query: Natural language search query (lowercase)

        Returns:
            Dictionary of filters to apply to queryset

        Raises:
            ParseError: If query cannot be interpreted

        Example:
            >>> SearchParser.parse("young males from nigeria")
            {
                'gender__exact': 'male',
                'age__gte': 16,
                'age__lte': 24,
                'country_id__exact': 'NG'
            }
        """
        query = query.lower().strip()
        filters = {}
        parsed = False

        # Parse gender
        if SearchParser._parse_gender(query, filters):
            parsed = True

        # Parse age groups
        if SearchParser._parse_age_group(query, filters):
            parsed = True

        # Parse age descriptors (young, old, etc.)
        if SearchParser._parse_age_descriptor(query, filters):
            parsed = True

        # Parse specific age ranges (above N)
        if SearchParser._parse_age_range(query, filters):
            parsed = True

        # Parse countries
        if SearchParser._parse_country(query, filters):
            parsed = True

        if not parsed:
            raise ParseError(
                "Unable to interpret query. Try keywords like: "
                "'male', 'female', 'teenager', 'adult', 'young', "
                "'nigeria', 'kenya', or 'above 30'"
            )

        return filters

    @staticmethod
    def _parse_gender(query: str, filters: Dict[str, Any]) -> bool:
        """
        Parse gender from query.

        Args:
            query: Search query
            filters: Filters dictionary to update

        Returns:
            True if gender was found and parsed
        """
        parsed = False

        has_male = "male" in query
        has_female = "female" in query

        # If both genders appear, do not constrain by gender
        if has_male and not has_female:
            filters["gender"] = "male"
            parsed = True
        elif has_female and not has_male:
            filters["gender"] = "female"
            parsed = True

        return parsed

    @staticmethod
    def _parse_age_group(query: str, filters: Dict[str, Any]) -> bool:
        """
        Parse age group from query.

        Args:
            query: Search query
            filters: Filters dictionary to update

        Returns:
            True if age group was found and parsed
        """
        parsed = False

        for age_group in FilterConstants.AGE_GROUP_CHOICES:
            if age_group in query:
                filters["age_group"] = age_group
                parsed = True
                break

        return parsed

    @staticmethod
    def _parse_age_descriptor(query: str, filters: Dict[str, Any]) -> bool:
        """
        Parse age descriptors like 'young', 'old'.

        Args:
            query: Search query
            filters: Filters dictionary to update

        Returns:
            True if age descriptor was found and parsed
        """
        parsed = False

        for descriptor, (min_age, max_age) in FilterConstants.AGE_RANGES.items():
            if descriptor in query:
                filters["age__gte"] = min_age
                filters["age__lte"] = max_age
                parsed = True
                break

        return parsed

    @staticmethod
    def _parse_age_range(query: str, filters: Dict[str, Any]) -> bool:
        """
        Parse explicit age ranges (above N, below N).

        Args:
            query: Search query
            filters: Filters dictionary to update

        Returns:
            True if age range was found and parsed
        """
        parsed = False

        # Pattern: "above N" or "older than N"
        above_match = re.search(r"above\s+(\d+)", query)
        if above_match:
            age = int(above_match.group(1))
            if FilterConstants.MIN_AGE <= age <= FilterConstants.MAX_AGE:
                filters["age__gte"] = age
                parsed = True

        # Pattern: "below N" or "younger than N"
        below_match = re.search(r"below\s+(\d+)", query)
        if below_match:
            age = int(below_match.group(1))
            if FilterConstants.MIN_AGE <= age <= FilterConstants.MAX_AGE:
                filters["age__lte"] = age
                parsed = True

        return parsed

    @staticmethod
    def _parse_country(query: str, filters: Dict[str, Any]) -> bool:
        """
        Parse country from query.

        Args:
            query: Search query
            filters: Filters dictionary to update

        Returns:
            True if country was found and parsed
        """
        parsed = False

        for country_name, country_code in FilterConstants.COUNTRY_MAPPING.items():
            if country_name in query:
                filters["country_id"] = country_code
                parsed = True
                break

        return parsed

    @staticmethod
    def build_queryset_filters(parsed_filters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert parsed filters to Django queryset filter format.

        Args:
            parsed_filters: Filters from parse()

        Returns:
            Dictionary ready for queryset.filter(**kwargs)

        Example:
            >>> parsed = SearchParser.parse("young males")
            >>> django_filters = SearchParser.build_queryset_filters(parsed)
            >>> Profile.objects.filter(**django_filters)
        """
        django_filters = {}

        for key, value in parsed_filters.items():
            if key.startswith("age__"):
                # Keep as is: age__gte, age__lte
                django_filters[key] = value
            elif key == "gender":
                django_filters["gender"] = value
            elif key == "country_id":
                django_filters["country_id"] = value
            elif key == "age_group":
                django_filters["age_group"] = value

        return django_filters
