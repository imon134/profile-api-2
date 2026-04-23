# PROFESSIONAL AUDIT REPORT
## Insighta Labs Demographics API - Stage 2 Implementation

**Date:** April 23, 2026  
**Audit Level:** Enterprise Standard  
**Current Score:** 10/100 (10.0%)  
**Pass Mark Required:** 75/100  

---

## EXECUTIVE SUMMARY

Your Django API implementation has **7 critical and architectural issues** preventing production readiness. The codebase demonstrates good foundational understanding (README passed 10/10), but fails on:

- **Data Integrity:** No seed data (only 1 vs 2026 profiles)
- **Response Format:** Pagination error handling breaks JSON envelope
- **Error Handling:** Inconsistent error responses violate spec
- **Enterprise Standards:** Missing production-grade patterns

**Estimated Fix Time:** 2-3 hours for all critical issues  
**Learning Value:** High — addresses common architectural mistakes

---

## SECTION 1: CRITICAL ISSUES (Causing Test Failures)

### Issue #1: MISSING SEED DATA ⚠️ CRITICAL

**Test Failure:** `"Unable to create seed profiles"` (7/8 tests fail)

#### Current Implementation
```json
// data/seed.json (WRONG)
{
  "profiles": [
    {
      "name": "john",
      "gender": "male",
      ...
    }
  ]
}
// Only 1 profile loaded, expected: 2026
```

#### Root Cause
The `ensure_seed()` function loads from `seed.json`, but the file contains only 1 sample profile. The grading system expects 2026 profiles to be seeded.

#### Expected Behavior
- `seed.json` must contain all 2026 demographic profiles
- Each profile must match the exact schema defined in requirements
- Running seed multiple times should not create duplicates (idempotent)

#### Professional Fix

**Step 1: Create proper seed data file**

You need to obtain the actual 2026 profiles from the provided data source. The file should look like:

```json
{
  "profiles": [
    {
      "name": "profile_name_1",
      "gender": "male|female",
      "gender_probability": 0.95,
      "age": 25,
      "age_group": "child|teenager|adult|senior",
      "country_id": "NG",
      "country_name": "Nigeria",
      "country_probability": 0.87
    },
    // ... 2025 more profiles
  ]
}
```

**Step 2: Fix idempotency**

Current implementation already checks `if Profile.objects.exists()` but there's a subtle issue: if seeding partially fails, it won't retry. Better approach:

```python
def ensure_seed():
    # Check if we have exactly 2026 profiles (idempotent)
    if Profile.objects.count() >= 2026:
        return
    
    # If partially seeded, clear and start fresh
    if Profile.objects.exists():
        Profile.objects.all().delete()
    
    with open(settings.BASE_DIR / "data/seed.json") as f:
        data = json.load(f).get("profiles", [])
    
    if len(data) < 2026:
        raise ValueError(f"Expected 2026 profiles, got {len(data)}")
    
    objs = []
    for p in data:
        objs.append(Profile(
            name=p["name"].strip().lower(),
            gender=p["gender"].lower(),
            gender_probability=float(p["gender_probability"]),
            age=int(p["age"]),
            age_group=p["age_group"].lower(),
            country_id=p["country_id"].upper(),
            country_name=p["country_name"],
            country_probability=float(p["country_probability"]),
        ))
    
    Profile.objects.bulk_create(objs, batch_size=1000)
```

**Why This Matters:**
- Grading script only seeds once, then runs tests
- 7 test categories depend on seed data
- Without 2026 profiles, all filtering/sorting/pagination tests fail

---

### Issue #2: PAGINATION ERROR HANDLING BUG ⚠️ CRITICAL

**Test Failure:** `"pagination envelope invalid for page=1&limit=5"`

#### Current Implementation (WRONG)
```python
# core/pagination.py
def paginate(qs, page, limit):
    try:
        page = int(page)
        limit = int(limit)
    except:
        return None, "Invalid query parameters"  # ❌ Returns string!
    
    if page < 1 or limit < 1:
        return None, "Invalid query parameters"  # ❌ Returns string!
    
    if limit > 50:
        limit = 50
    
    return qs[start:end], {
        "page": page,
        "limit": limit,
        "total": total
    }

# views.py
def get_profiles(request):
    result, meta = paginate(qs, page, limit)
    if result is None:
        return error(meta, 422)  # ❌ meta is a STRING, not an error message!
```

#### The Problem
When pagination fails:
1. `paginate()` returns `(None, "Invalid query parameters")`  
2. Views pass the string to `error()` function
3. Error response becomes: `{"status": "error", "message": "Invalid query parameters"}`
4. But grader expects consistent error structure

#### Expected Response (Correct)
```json
{
  "status": "error",
  "message": "Invalid query parameters"
}
```

#### Professional Fix

**Refactored pagination with proper error handling:**

```python
# core/pagination.py
class PaginationError(Exception):
    """Custom exception for pagination errors"""
    pass

def paginate(qs, page, limit):
    """
    Paginate queryset with validation.
    
    Raises:
        PaginationError: If page or limit are invalid
    
    Returns:
        (queryset, metadata_dict)
    """
    try:
        page = int(page)
        limit = int(limit)
    except (TypeError, ValueError):
        raise PaginationError("page and limit must be integers")
    
    # Validate page and limit
    if page < 1:
        raise PaginationError("page must be >= 1")
    if limit < 1:
        raise PaginationError("limit must be >= 1")
    
    # Cap limit to max 50
    if limit > 50:
        limit = 50
    
    total = qs.count()
    start = (page - 1) * limit
    end = start + limit
    
    return qs[start:end], {
        "page": page,
        "limit": limit,
        "total": total
    }

# views.py
def get_profiles(request):
    ensure_seed()
    qs = Profile.objects.all()
    
    # ... filtering and sorting ...
    
    # PAGINATION with proper error handling
    try:
        page = request.GET.get("page", 1)
        limit = request.GET.get("limit", 10)
        result, meta = paginate(qs, page, limit)
    except PaginationError as e:
        return error(str(e), 400)  # ✅ Proper error handling
    except Exception as e:
        return error("Server error", 500)
    
    data = [serialize(p) for p in result]
    return success(data, meta)
```

**Why This Matters:**
- HTTP spec: 400 Bad Request = client error (invalid page/limit)
- Proper error structure is required by grading script
- Error messages must be strings, not objects

---

### Issue #3: SORT VALIDATION ERROR RESPONSE ⚠️ CRITICAL

**Test Failure:** `"invalid sort_by did not return expected error envelope"`

#### Current Implementation (WRONG)
```python
# views.py
allowed = ["age", "created_at", "gender_probability"]

if sort_by not in allowed:
    return error("Invalid query parameters", 422)  # ❌ Status 422?

if order not in ["asc", "desc"]:
    return error("Invalid query parameters", 422)  # ❌ Status 422?
```

#### The Problem
1. **Status Code**: 422 (Unprocessable Entity) is for semantic errors, not validation
2. **Appropriate Status**: 400 (Bad Request) for invalid parameters
3. **Spec says**: Invalid parameters should return 400

#### Expected Behavior
```
Request: /api/profiles?sort_by=invalid_field
Response: 400 Bad Request
{
  "status": "error",
  "message": "sort_by must be one of: age, created_at, gender_probability"
}
```

#### Professional Fix
```python
# core/constants.py (NEW FILE - Enterprise pattern)
class QueryConstants:
    ALLOWED_SORT_FIELDS = ["age", "created_at", "gender_probability"]
    ALLOWED_ORDERS = ["asc", "desc"]
    MAX_LIMIT = 50
    DEFAULT_PAGE = 1
    DEFAULT_LIMIT = 10
    
    @staticmethod
    def validate_sort_by(sort_by):
        if sort_by not in QueryConstants.ALLOWED_SORT_FIELDS:
            raise ValueError(
                f"sort_by must be one of: {', '.join(QueryConstants.ALLOWED_SORT_FIELDS)}"
            )
    
    @staticmethod
    def validate_order(order):
        if order not in QueryConstants.ALLOWED_ORDERS:
            raise ValueError(f"order must be 'asc' or 'desc'")

# views.py (REFACTORED)
def get_profiles(request):
    ensure_seed()
    qs = Profile.objects.all()
    
    # ... filters ...
    
    # SORTING with proper validation
    sort_by = request.GET.get("sort_by", "created_at")
    order = request.GET.get("order", "asc")
    
    try:
        QueryConstants.validate_sort_by(sort_by)
        QueryConstants.validate_order(order)
    except ValueError as e:
        return error(str(e), 400)  # ✅ Use 400 for invalid parameters
    
    if order == "desc":
        sort_by = f"-{sort_by}"
    
    qs = qs.order_by(sort_by)
    
    # ... pagination ...
```

---

### Issue #4: SEARCH ENDPOINT ERROR HANDLING ⚠️ CRITICAL

**Test Failure:** `"uninterpretable q did not return expected error envelope"`

#### Current Implementation (WRONG)
```python
# views.py
def search_profiles(request):
    q = request.GET.get("q", "").lower()
    
    if not q:
        return error("Missing or empty parameter", 400)  # ❌ 400 is OK
    
    # ... parsing logic ...
    
    if not parsed:
        return error("Unable to interpret query", 422)  # ❌ Should be 400!
```

#### The Problem
1. **Status 422** means "I understand the syntax but can't process the semantics"
2. **For "unable to interpret"**: This is really a malformed request → **400**
3. **Inconsistency**: Similar error should be 400 to match sort_by handling

#### Professional Fix
```python
def search_profiles(request):
    ensure_seed()
    
    q = request.GET.get("q", "").strip().lower()
    
    # Validate required parameter
    if not q:
        return error("Missing required parameter: q", 400)
    
    qs = Profile.objects.all()
    parsed = False
    
    # ... parsing logic unchanged ...
    
    if not parsed:
        return error(
            "Unable to interpret query. Try: 'male teenagers from Nigeria' or 'females above 30'",
            400  # ✅ Use 400 for uninterpretable queries
        )
    
    # ... pagination with error handling ...
```

**Why This Matters:**
- HTTP semantics: 400 = "request is malformed", 422 = "request is well-formed but semantically wrong"
- Consistency across endpoints
- Grading script validates exact error envelopes

---

## SECTION 2: ARCHITECTURE ISSUES

### Issue #5: No Database Indexes ⚠️ PERFORMANCE

**Problem:** Frequently filtered fields have no indexes

#### Current Model (MISSING OPTIMIZATION)
```python
# WRONG - No indexes
class Profile(models.Model):
    name = models.CharField(max_length=255, unique=True)
    gender = models.CharField(max_length=10)  # ❌ No index
    age_group = models.CharField(max_length=20)  # ❌ No index
    country_id = models.CharField(max_length=2)  # ❌ No index
    age = models.IntegerField()  # ❌ No index for range queries
```

#### Enterprise Fix
```python
class Profile(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid7, editable=False)
    name = models.CharField(
        max_length=255, 
        unique=True,
        db_index=True,  # ✅ For name searches
        help_text="Full name, stored lowercase"
    )
    
    gender = models.CharField(
        max_length=10,
        db_index=True,  # ✅ Frequently filtered
        choices=[('male', 'Male'), ('female', 'Female')]
    )
    gender_probability = models.FloatField()
    
    age = models.IntegerField(
        db_index=True  # ✅ For range queries (min_age, max_age)
    )
    age_group = models.CharField(
        max_length=20,
        db_index=True,  # ✅ Frequently filtered
        choices=[
            ('child', 'Child'),
            ('teenager', 'Teenager'),
            ('adult', 'Adult'),
            ('senior', 'Senior')
        ]
    )
    
    country_id = models.CharField(
        max_length=2,
        db_index=True,  # ✅ Frequently filtered
        help_text="ISO 3166-1 alpha-2 country code"
    )
    country_name = models.CharField(max_length=100)
    country_probability = models.FloatField()
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True  # ✅ For sorting
    )
    
    class Meta:
        # Composite indexes for common filter combinations
        indexes = [
            models.Index(fields=['gender', 'country_id']),
            models.Index(fields=['age_group', 'age']),
        ]
        verbose_name_plural = "profiles"
    
    def __str__(self):
        return f"{self.name} ({self.age}, {self.country_name})"
```

**Migration Commands:**
```bash
python manage.py makemigrations
python manage.py migrate
```

---

### Issue #6: No Constants/Configuration Management ⚠️ CODE QUALITY

**Problem:** Magic strings scattered throughout codebase

#### Current Implementation (WRONG)
```python
# Scattered in views.py
allowed = ["age", "created_at", "gender_probability"]
countries = {
    "nigeria": "NG",
    "kenya": "KE",
    # ...
}
```

#### Enterprise Fix: Create Configuration Layer

```python
# profiles/core/constants.py (NEW FILE)
"""
Query parameters and parsing configuration.
This is the single source of truth for all query validation.
"""

class FilterConstants:
    """Allowed filter fields and their configurations"""
    
    # Field definitions
    GENDER_CHOICES = ('male', 'female')
    AGE_GROUP_CHOICES = ('child', 'teenager', 'adult', 'senior')
    
    # Sorting
    ALLOWED_SORT_FIELDS = ['age', 'created_at', 'gender_probability']
    ALLOWED_ORDERS = ['asc', 'desc']
    DEFAULT_SORT_BY = 'created_at'
    DEFAULT_ORDER = 'asc'
    
    # Pagination
    DEFAULT_PAGE = 1
    DEFAULT_LIMIT = 10
    MAX_LIMIT = 50
    
    # Natural language parsing
    COUNTRY_MAPPING = {
        'nigeria': 'NG',
        'kenya': 'KE',
        'ghana': 'GH',
        'uganda': 'UG',
        'tanzania': 'TZ',
        'angola': 'AO',
        'benin': 'BJ',
    }
    
    AGE_GROUP_MAPPING = {
        'child': 'child',
        'children': 'child',
        'teenager': 'teenager',
        'teenagers': 'teenager',
        'teen': 'teenager',
        'teens': 'teenager',
        'adult': 'adult',
        'adults': 'adult',
        'senior': 'senior',
        'seniors': 'senior',
        'elderly': 'senior',
    }
    
    # Age range definitions for natural language
    AGE_RANGES = {
        'young': (16, 24),      # "young" = 16-24
        'middle-aged': (35, 55),
        'old': (65, 100),
    }
```

#### Usage in Views
```python
# profiles/views.py
from profiles.core.constants import FilterConstants

def get_profiles(request):
    sort_by = request.GET.get(
        "sort_by", 
        FilterConstants.DEFAULT_SORT_BY
    )
    
    if sort_by not in FilterConstants.ALLOWED_SORT_FIELDS:
        return error(
            f"sort_by must be one of: {', '.join(FilterConstants.ALLOWED_SORT_FIELDS)}",
            400
        )
```

---

### Issue #7: No Request Validation Layer ⚠️ CODE QUALITY

**Problem:** Parameter validation scattered in views

#### Enterprise Fix: Create Validators Module

```python
# profiles/core/validators.py (ENHANCED)
"""
Request parameter validation and type conversion.
Centralized validation reduces code duplication and improves maintainability.
"""

from typing import Optional, Tuple, Dict, Any
from profiles.core.constants import FilterConstants

class ValidationError(Exception):
    """Raised when parameter validation fails"""
    def __init__(self, message: str, status_code: int = 400):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class QueryValidator:
    """Validates query parameters for /api/profiles endpoint"""
    
    @staticmethod
    def to_int(value: Any, field_name: str) -> Optional[int]:
        """Convert value to int, raise ValidationError if invalid"""
        if value is None:
            return None
        try:
            return int(value)
        except (ValueError, TypeError):
            raise ValidationError(f"{field_name} must be an integer", 400)
    
    @staticmethod
    def to_float(value: Any, field_name: str) -> Optional[float]:
        """Convert value to float, raise ValidationError if invalid"""
        if value is None:
            return None
        try:
            return float(value)
        except (ValueError, TypeError):
            raise ValidationError(f"{field_name} must be a decimal number", 400)
    
    @staticmethod
    def validate_gender(gender: Optional[str]) -> Optional[str]:
        """Validate gender parameter"""
        if gender is None:
            return None
        if gender.lower() not in FilterConstants.GENDER_CHOICES:
            raise ValidationError(
                f"gender must be 'male' or 'female', got '{gender}'",
                400
            )
        return gender.lower()
    
    @staticmethod
    def validate_age_group(age_group: Optional[str]) -> Optional[str]:
        """Validate age_group parameter"""
        if age_group is None:
            return None
        if age_group.lower() not in FilterConstants.AGE_GROUP_CHOICES:
            raise ValidationError(
                f"age_group must be one of: {', '.join(FilterConstants.AGE_GROUP_CHOICES)}",
                400
            )
        return age_group.lower()
    
    @staticmethod
    def validate_sort_by(sort_by: str) -> str:
        """Validate sort_by parameter"""
        if sort_by not in FilterConstants.ALLOWED_SORT_FIELDS:
            raise ValidationError(
                f"sort_by must be one of: {', '.join(FilterConstants.ALLOWED_SORT_FIELDS)}",
                400
            )
        return sort_by
    
    @staticmethod
    def validate_order(order: str) -> str:
        """Validate order parameter"""
        if order not in FilterConstants.ALLOWED_ORDERS:
            raise ValidationError(f"order must be 'asc' or 'desc', got '{order}'", 400)
        return order
    
    @staticmethod
    def validate_pagination(
        page: str = "1",
        limit: str = "10"
    ) -> Tuple[int, int]:
        """
        Validate and return pagination parameters.
        
        Returns:
            (page, limit) tuple
        
        Raises:
            ValidationError
        """
        page_int = QueryValidator.to_int(page, "page")
        limit_int = QueryValidator.to_int(limit, "limit")
        
        if page_int < 1:
            raise ValidationError("page must be >= 1", 400)
        if limit_int < 1:
            raise ValidationError("limit must be >= 1", 400)
        
        # Cap limit at MAX_LIMIT
        limit_int = min(limit_int, FilterConstants.MAX_LIMIT)
        
        return page_int, limit_int
```

---

### Issue #8: No Centralized Error Handling ⚠️ CODE QUALITY

**Problem:** Error responses inconsistent across endpoints

#### Enterprise Fix: Error Handling Middleware

```python
# profiles/core/errors.py (NEW FILE)
"""
Centralized error handling with consistent response format.
"""

from django.http import JsonResponse
from typing import Tuple

class APIError(Exception):
    """Base class for API errors"""
    def __init__(self, message: str, status_code: int = 500):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class ValidationError(APIError):
    """Invalid query parameters"""
    def __init__(self, message: str):
        super().__init__(message, 400)


class NotFoundError(APIError):
    """Resource not found"""
    def __init__(self, message: str = "Resource not found"):
        super().__init__(message, 404)


class ServerError(APIError):
    """Internal server error"""
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
            "message": message
        },
        status=status_code
    )


def success_response(
    data: list,
    page: int,
    limit: int,
    total: int
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
            "data": data
        },
        status=200
    )
```

---

### Issue #9: No Input Sanitization ⚠️ SECURITY

**Problem:** Search query parsing uses regex without sanitization

#### Current Implementation (RISKY)
```python
# views.py
q = request.GET.get("q", "").lower()
# ... direct string matching on user input ...
match = re.search(r"above (\d+)", q)  # Could be exploited
```

#### Enterprise Fix: Add Sanitization

```python
# profiles/core/validators.py (ADD TO EXISTING FILE)
import re

class SearchValidator:
    """Validates natural language search queries"""
    
    MAX_QUERY_LENGTH = 500
    ALLOWED_PATTERN = re.compile(r'^[a-z0-9\s\-]+$', re.IGNORECASE)
    
    @staticmethod
    def validate_search_query(q: str) -> str:
        """
        Validate search query.
        
        Args:
            q: Search query string
        
        Returns:
            Sanitized query
        
        Raises:
            ValidationError: If query is invalid
        """
        if not q or not q.strip():
            raise ValidationError("Search query cannot be empty", 400)
        
        q = q.strip().lower()
        
        # Length check
        if len(q) > SearchValidator.MAX_QUERY_LENGTH:
            raise ValidationError(
                f"Search query too long (max {SearchValidator.MAX_QUERY_LENGTH} characters)",
                400
            )
        
        # Pattern check: only alphanumeric, spaces, hyphens
        if not SearchValidator.ALLOWED_PATTERN.match(q):
            raise ValidationError(
                "Search query contains invalid characters. Use only letters, numbers, spaces, and hyphens.",
                400
            )
        
        return q
```

---

## SECTION 3: CODE QUALITY ISSUES

### Issue #10: Missing Logging ⚠️ OBSERVABILITY

**Problem:** No logging for debugging in production

#### Enterprise Fix: Add Logging

```python
# profiles/core/logger.py (NEW FILE)
import logging
import sys
from logging.handlers import RotatingFileHandler

def get_logger(name: str) -> logging.Logger:
    """Get configured logger instance"""
    logger = logging.getLogger(name)
    
    if not logger.handlers:
        # Console handler
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(
            logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
        )
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    
    return logger

# Usage in views
import logging
logger = logging.getLogger(__name__)

def get_profiles(request):
    logger.info(f"GET /api/profiles - params: {request.GET.dict()}")
    try:
        # ... endpoint logic ...
    except Exception as e:
        logger.error(f"Error in get_profiles: {str(e)}", exc_info=True)
        raise
```

---

### Issue #11: No Type Hints ⚠️ CODE QUALITY

**Problem:** Functions lack type annotations (enterprise requirement)

#### Current (WRONG)
```python
def paginate(qs, page, limit):  # ❌ No type hints
    # ...
```

#### Enterprise Fix
```python
from typing import Tuple, Dict, Any, Optional
from django.db.models import QuerySet

def paginate(
    qs: QuerySet,
    page: int,
    limit: int
) -> Tuple[QuerySet, Dict[str, Any]]:
    """
    Paginate a queryset.
    
    Args:
        qs: Django QuerySet to paginate
        page: Page number (1-indexed)
        limit: Items per page
    
    Returns:
        (paginated_queryset, metadata_dict)
    
    Raises:
        ValidationError: If page or limit are invalid
    """
    # ...
```

---

### Issue #12: Missing Docstrings ⚠️ DOCUMENTATION

**Problem:** No documentation for functions/classes

#### Enterprise Fix
```python
def get_profiles(request: HttpRequest) -> JsonResponse:
    """
    Get all profiles with filtering, sorting, and pagination.
    
    Query Parameters:
        - gender (str): 'male' or 'female'
        - age_group (str): 'child', 'teenager', 'adult', or 'senior'
        - country_id (str): ISO country code (e.g., 'NG')
        - min_age (int): Minimum age inclusive
        - max_age (int): Maximum age inclusive
        - min_gender_probability (float): Minimum gender confidence (0.0-1.0)
        - min_country_probability (float): Minimum country confidence (0.0-1.0)
        - sort_by (str): Field to sort by (age, created_at, gender_probability)
        - order (str): Sort order ('asc' or 'desc')
        - page (int): Page number (default: 1)
        - limit (int): Items per page (default: 10, max: 50)
    
    Returns:
        JsonResponse with success envelope:
        {
            "status": "success",
            "page": int,
            "limit": int,
            "total": int,
            "data": [Profile, ...]
        }
    
    Raises:
        400 Bad Request: Invalid parameters
        500 Internal Server Error: Database error
    
    Example:
        GET /api/profiles?gender=male&country_id=NG&page=1&limit=10
    """
```

---

## SECTION 4: DATABASE SCHEMA GAPS

### Issue #13: No Validation Constraints ⚠️ DATA INTEGRITY

**Current Model (INCOMPLETE)**
```python
gender = models.CharField(max_length=10)  # ❌ Any string accepted
age = models.IntegerField()  # ❌ Negative ages allowed
```

#### Enterprise Fix
```python
from django.core.validators import MinValueValidator, MaxValueValidator

class Profile(models.Model):
    gender = models.CharField(
        max_length=10,
        choices=[
            ('male', 'Male'),
            ('female', 'Female'),
        ],
        db_index=True
    )
    
    gender_probability = models.FloatField(
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)]
    )
    
    age = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(150)],
        db_index=True
    )
    
    age_group = models.CharField(
        max_length=20,
        choices=[
            ('child', 'Child (0-12)'),
            ('teenager', 'Teenager (13-19)'),
            ('adult', 'Adult (20-64)'),
            ('senior', 'Senior (65+)'),
        ],
        db_index=True
    )
    
    country_probability = models.FloatField(
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)]
    )
```

---

## SECTION 5: ENTERPRISE BEST PRACTICES MISSING

### Issue #14: No API Documentation ⚠️ MISSING

**Fix:** Add Swagger/OpenAPI documentation

```python
# profiles/views.py (Use drf-spectacular)
from drf_spectacular.utils import extend_schema

@extend_schema(
    operation_id="list_profiles",
    description="Retrieve all profiles with filtering, sorting, and pagination",
    parameters=[
        OpenApiParameter(name="gender", type=str, description="Filter by gender"),
        OpenApiParameter(name="page", type=int, description="Page number"),
        # ... more parameters ...
    ],
    responses=ProfileListSerializer
)
def get_profiles(request):
    # ...
```

---

### Issue #15: No Tests ⚠️ CRITICAL FOR PRODUCTION

**Create test file:** `profiles/tests/test_endpoints.py`

```python
from django.test import TestCase, Client
from profiles.models import Profile
import json

class ProfileEndpointTests(TestCase):
    
    def setUp(self):
        self.client = Client()
        # Create test profiles
        Profile.objects.create(
            name="john doe",
            gender="male",
            gender_probability=0.98,
            age=25,
            age_group="adult",
            country_id="NG",
            country_name="Nigeria",
            country_probability=0.87
        )
    
    def test_get_profiles_success(self):
        response = self.client.get('/api/profiles')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['status'], 'success')
        self.assertEqual(len(data['data']), 1)
    
    def test_invalid_sort_by(self):
        response = self.client.get('/api/profiles?sort_by=invalid')
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertEqual(data['status'], 'error')
    
    def test_pagination_limit_capped(self):
        response = self.client.get('/api/profiles?limit=100')
        data = json.loads(response.content)
        self.assertEqual(data['limit'], 50)  # Max capped at 50
    
    def test_search_query_invalid(self):
        response = self.client.get('/api/profiles/search?q=xyz123!@#')
        self.assertEqual(response.status_code, 400)
```

---

## SECTION 6: PERFORMANCE OPTIMIZATION

### Issue #16: No Query Optimization ⚠️ PERFORMANCE

**Problem:** N+1 queries possible; no select_related/prefetch_related

```python
# WRONG - Could cause N+1 queries
for profile in profiles:
    # Each profile access causes new query
    print(profile.country_name)
```

#### Fix: Use select_related when appropriate

```python
# For foreign key fields (if implemented later)
qs = Profile.objects.select_related('country')

# Use only() to reduce columns fetched
qs = Profile.objects.only(
    'id', 'name', 'gender', 'age', 'country_id',
    'age_group', 'created_at'
)
```

---

### Issue #17: No Caching Strategy ⚠️ PERFORMANCE

**Problem:** Same queries executed repeatedly

#### Enterprise Fix: Add Redis Caching

```python
# settings.py
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/1',
    }
}

# views.py (with caching)
from django.views.decorators.cache import cache_page

@cache_page(60 * 5)  # Cache for 5 minutes
def get_profiles(request):
    # ... endpoint logic ...
```

---

## SECTION 7: SUMMARY OF FIXES

### Critical Fixes Required (To Pass)

| Issue | Status Code | Fix |
|-------|-------------|-----|
| Missing 2026 profiles | N/A | Populate seed.json with full dataset |
| Pagination error format | 422 | Use PaginationError exception, return 400 |
| Invalid sort_by status | 422 | Return 400 instead of 422 |
| Search query status | 422 | Return 400 instead of 422 |
| Error messages | 500 | Ensure all errors return valid JSON envelope |

### Enterprise Improvements (For Production)

1. **Database Indexes** - Add db_index to filtered fields
2. **Constants Layer** - Centralize configuration
3. **Request Validation** - Centralized validators
4. **Error Handling** - Consistent error responses
5. **Type Hints** - All functions annotated
6. **Docstrings** - Complete documentation
7. **Logging** - Debug production issues
8. **Tests** - Unit and integration tests
9. **API Docs** - Swagger/OpenAPI

---

## SECTION 8: RECOMMENDED FILE STRUCTURE

```
profiles/
├── models.py                  # ✅ Existing, needs indexes
├── views.py                   # ✅ Needs refactoring
├── urls.py                    # ✅ OK
├── core/
│   ├── __init__.py
│   ├── constants.py           # 🆕 NEW - Configuration
│   ├── validators.py          # ✅ Needs enhancement
│   ├── errors.py              # 🆕 NEW - Error handling
│   ├── logger.py              # 🆕 NEW - Logging
│   ├── pagination.py          # ✅ Needs refactoring
│   ├── serializers.py         # ✅ OK
│   ├── seed.py                # ✅ Needs enhancement
│   └── search_parser.py       # 🆕 NEW - Separate search logic
├── management/
│   └── commands/
│       └── seed_profiles.py   # 🆕 NEW - Proper Django command
└── tests/
    ├── __init__.py
    ├── test_endpoints.py      # 🆕 NEW - Endpoint tests
    ├── test_serializers.py    # 🆕 NEW - Serializer tests
    └── test_validators.py     # 🆕 NEW - Validator tests
```

---

## NEXT STEPS

1. **Immediate** (1 hour):
   - Obtain and populate seed.json with 2026 profiles
   - Fix pagination error handling (use exception pattern)
   - Change sort_by and search error status to 400

2. **Short-term** (2-3 hours):
   - Add database indexes
   - Create constants.py file
   - Refactor error handling
   - Add input validation

3. **Medium-term** (4-6 hours):
   - Add type hints
   - Write comprehensive tests
   - Add logging
   - Create API documentation

4. **Long-term** (Production):
   - Set up CI/CD pipeline
   - Add monitoring/alerting
   - Implement caching strategy
   - Create deployment documentation

---

## LEARNING TAKEAWAYS

### ✅ What You Did Right
1. UUID v7 implementation (custom but functional)
2. Basic filtering/sorting logic
3. CORS configuration
4. Bulk create for performance
5. Graceful error handling foundation

### ❌ What Needs Improvement
1. Error handling pattern (using exceptions > return tuples)
2. Configuration management (centralize constants)
3. HTTP status code semantics (400 vs 422)
4. Input validation (create dedicated validators)
5. Enterprise standards (tests, logging, docs)

### 🎯 Key Enterprise Principles
1. **Single Responsibility**: Each module has one job
2. **DRY** (Don't Repeat Yourself): Constants centralized
3. **Fail Fast**: Validate at API boundary
4. **Error Clarity**: Helpful error messages
5. **Observability**: Logging and monitoring
6. **Tests First**: Tests define expected behavior
7. **Documentation**: Code should explain itself

---

**End of Professional Audit Report**

*This audit provides enterprise-standard feedback. Implementing these recommendations will significantly improve code quality, maintainability, and production readiness.*
