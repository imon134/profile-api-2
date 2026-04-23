"""
Profile API endpoints for demographic intelligence queries.
Provides filtering, sorting, pagination, and natural language search.
"""

from django.http import HttpRequest, JsonResponse
from django.views.decorators.http import require_http_methods
from typing import Optional

from profiles.models import Profile
from profiles.core.seed import ensure_seed
from profiles.core.pagination import paginate, PaginationError
from profiles.core.serializers import serialize_multiple
from profiles.core.errors import (
    error_response,
    success_response,
    ValidationError,
    ParseError,
)
from profiles.core.validators import QueryValidator, SearchValidator, to_int, to_float
from profiles.core.constants import FilterConstants
from profiles.core.search_parser import SearchParser
from profiles.core.logger import get_logger

logger = get_logger(__name__)


@require_http_methods(["GET"])
def get_profiles(request: HttpRequest) -> JsonResponse:
    """
    Retrieve profiles with advanced filtering, sorting, and pagination.

    Query Parameters:
        Filters:
        - gender (str): 'male' or 'female'
        - age_group (str): 'child', 'teenager', 'adult', or 'senior'
        - country_id (str): ISO country code (e.g., 'NG')
        - min_age (int): Minimum age (inclusive)
        - max_age (int): Maximum age (inclusive)
        - min_gender_probability (float): Minimum gender confidence (0.0-1.0)
        - min_country_probability (float): Minimum country confidence (0.0-1.0)

        Sorting:
        - sort_by (str): Field to sort by (age, created_at, gender_probability)
        - order (str): Sort order ('asc' or 'desc')

        Pagination:
        - page (int): Page number (default: 1)
        - limit (int): Items per page (default: 10, max: 50)

    Returns:
        JsonResponse with structure:
        {
            "status": "success",
            "page": int,
            "limit": int,
            "total": int,
            "data": [Profile, ...]
        }

    Status Codes:
        200: Success
        400: Bad Request (invalid parameters)
        500: Internal Server Error
    """
    logger.info(f"GET /api/profiles - params: {request.GET.dict()}")

    try:
        # Ensure database is seeded
        ensure_seed()

        # Start with all profiles
        qs = Profile.objects.all()

        # APPLY FILTERS
        try:
            # Gender filter
            gender = QueryValidator.validate_gender(request.GET.get("gender"))
            if gender:
                qs = qs.filter(gender=gender)
                logger.debug(f"Applied gender filter: {gender}")

            # Age group filter
            age_group = QueryValidator.validate_age_group(request.GET.get("age_group"))
            if age_group:
                qs = qs.filter(age_group=age_group)
                logger.debug(f"Applied age_group filter: {age_group}")

            # Country ID filter
            country_id = QueryValidator.validate_country_id(request.GET.get("country_id"))
            if country_id:
                qs = qs.filter(country_id=country_id)
                logger.debug(f"Applied country_id filter: {country_id}")

            # Min age filter
            min_age_str = request.GET.get("min_age")
            if min_age_str:
                min_age = to_int(min_age_str, "min_age")
                QueryValidator.validate_min_age(min_age)
                qs = qs.filter(age__gte=min_age)
                logger.debug(f"Applied min_age filter: {min_age}")

            # Max age filter
            max_age_str = request.GET.get("max_age")
            if max_age_str:
                max_age = to_int(max_age_str, "max_age")
                QueryValidator.validate_max_age(max_age)
                qs = qs.filter(age__lte=max_age)
                logger.debug(f"Applied max_age filter: {max_age}")

            # Min gender probability filter
            min_gp_str = request.GET.get("min_gender_probability")
            if min_gp_str:
                min_gp = to_float(min_gp_str, "min_gender_probability")
                QueryValidator.validate_gender_probability(min_gp)
                qs = qs.filter(gender_probability__gte=min_gp)
                logger.debug(f"Applied min_gender_probability filter: {min_gp}")

            # Min country probability filter
            min_cp_str = request.GET.get("min_country_probability")
            if min_cp_str:
                min_cp = to_float(min_cp_str, "min_country_probability")
                QueryValidator.validate_country_probability(min_cp)
                qs = qs.filter(country_probability__gte=min_cp)
                logger.debug(f"Applied min_country_probability filter: {min_cp}")

        except ValidationError as e:
            logger.warning(f"Validation error: {e.message}")
            return error_response(e.message, e.status_code)

        # APPLY SORTING
        try:
            sort_by = QueryValidator.validate_sort_by(
                request.GET.get("sort_by", FilterConstants.DEFAULT_SORT_BY)
            )
            order = QueryValidator.validate_order(
                request.GET.get("order", FilterConstants.DEFAULT_ORDER)
            )

            # Apply descending order prefix if needed
            if order == "desc":
                sort_by = f"-{sort_by}"

            qs = qs.order_by(sort_by)
            logger.debug(f"Applied sorting: {sort_by}, order: {order}")

        except ValidationError as e:
            logger.warning(f"Sorting validation error: {e.message}")
            return error_response(e.message, e.status_code)

        # APPLY PAGINATION
        try:
            page = request.GET.get("page", FilterConstants.DEFAULT_PAGE)
            limit = request.GET.get("limit", FilterConstants.DEFAULT_LIMIT)

            result, meta = paginate(qs, page, limit)
            logger.debug(f"Paginated results: page={meta['page']}, limit={meta['limit']}")

        except PaginationError as e:
            logger.warning(f"Pagination error: {e.message}")
            return error_response(e.message, e.status_code)

        # SERIALIZE AND RETURN
        data = serialize_multiple(result)
        logger.info(
            f"Successfully retrieved {len(data)} profiles (total: {meta['total']})"
        )
        return success_response(data, meta["page"], meta["limit"], meta["total"])

    except Exception as e:
        logger.error(f"Unexpected error in get_profiles: {str(e)}", exc_info=True)
        return error_response("Internal server error", 500)


@require_http_methods(["GET"])
def search_profiles(request: HttpRequest) -> JsonResponse:
    """
    Search profiles using natural language query.

    Converts plain English queries into database filters using rule-based parsing.

    Query Parameters:
        - q (str, required): Natural language search query
        - page (int): Page number (default: 1)
        - limit (int): Items per page (default: 10, max: 50)

    Supported Query Patterns:
        - Gender: "male", "female"
        - Age groups: "child", "teenager", "adult", "senior"
        - Age descriptors: "young" (16-24), "above 30"
        - Countries: "nigeria", "kenya", "ghana", "uganda", "tanzania", "angola", "benin"
        - Combined: "young males from nigeria", "female teenagers from kenya"

    Returns:
        JsonResponse with same structure as get_profiles endpoint

    Status Codes:
        200: Success
        400: Bad Request (missing/invalid query)
        500: Internal Server Error

    Examples:
        - /api/profiles/search?q=young+males+from+nigeria
        - /api/profiles/search?q=female+teenagers
        - /api/profiles/search?q=adults+above+30
    """
    logger.info(f"GET /api/profiles/search - query: {request.GET.get('q')}")

    try:
        # Ensure database is seeded
        ensure_seed()

        # Validate and sanitize query
        try:
            q = SearchValidator.validate_search_query(request.GET.get("q"))
        except ValidationError as e:
            logger.warning(f"Search query validation error: {e.message}")
            return error_response(e.message, e.status_code)

        # Parse natural language query
        try:
            parsed_filters = SearchParser.parse(q)
            logger.info(f"Parsed query '{q}' into filters: {parsed_filters}")
        except ParseError as e:
            logger.warning(f"Parse error: {e.message}")
            return error_response(e.message, e.status_code)

        # Apply filters to queryset
        qs = Profile.objects.all()
        for key, value in parsed_filters.items():
            if key.startswith("age__"):
                # Handle age range filters
                qs = qs.filter(**{key: value})
            else:
                # Handle exact match filters
                qs = qs.filter(**{key: value})

        logger.debug(f"Applied search filters, query count: {qs.count()}")

        # APPLY PAGINATION (same as get_profiles)
        try:
            page = request.GET.get("page", FilterConstants.DEFAULT_PAGE)
            limit = request.GET.get("limit", FilterConstants.DEFAULT_LIMIT)

            result, meta = paginate(qs, page, limit)

        except PaginationError as e:
            logger.warning(f"Pagination error in search: {e.message}")
            return error_response(e.message, e.status_code)

        # SERIALIZE AND RETURN
        data = serialize_multiple(result)
        logger.info(
            f"Search returned {len(data)} profiles (total: {meta['total']}) for query '{q}'"
        )
        return success_response(data, meta["page"], meta["limit"], meta["total"])

    except Exception as e:
        logger.error(f"Unexpected error in search_profiles: {str(e)}", exc_info=True)
        return error_response("Internal server error", 500)