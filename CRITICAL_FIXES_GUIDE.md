# IMPLEMENTATION GUIDE: Critical Fixes
## Get From 10/100 to 75/100+

This guide walks through implementing the critical fixes in order of impact.

---

## PREREQUISITE: Understand the Test Failures

```
✗ filtering_logic: 0/20 pts       → Needs seed data
✗ combined_filters: 0/15 pts      → Needs seed data  
✗ sorting: 0/10 pts               → Needs seed data
✗ pagination: 0/15 pts            → Invalid envelope + limit behavior
✗ natural_language_parsing: 0/20  → Needs seed data
✗ performance: 0/5 pts            → Needs seed data
✗ query_validation: 0/5 pts       → Error envelope issues
✓ readme_explanation: 10/10 pts   → PASS
```

**Root Causes:**
1. No seed data (2026 profiles missing) → affects 6 tests
2. Wrong error response format → affects 1 test
3. Wrong HTTP status codes → affects 1 test

---

## FIX #1: SEED DATA (PRIORITY: 🔴 CRITICAL)

**Impact:** Fixes 6/8 tests immediately

### Step 1: Get the Actual Data

The task mentions: "Seed your database with the 2026 profiles from this file: [link]"

**You need to:**
- Find the provided seed file from the task description
- Download it to `data/seed.json`
- Verify it has exactly 2026 profiles

### Step 2: Verify Data Structure

Check that the seed file matches this schema:

```json
{
  "profiles": [
    {
      "name": "string (lowercase)",
      "gender": "male|female",
      "gender_probability": float (0.0-1.0),
      "age": integer (0-150),
      "age_group": "child|teenager|adult|senior",
      "country_id": "XX (ISO code)",
      "country_name": "string",
      "country_probability": float (0.0-1.0)
    },
    // ... 2025 more ...
  ]
}
```

### Step 3: Test Seeding

```bash
# Terminal
cd /Users/esther/HNG\ project\ 2

# Clear existing data
python manage.py shell
>>> from profiles.models import Profile
>>> Profile.objects.all().delete()
>>> exit()

# Test seed loading
python manage.py shell
>>> from profiles.core.seed import ensure_seed
>>> ensure_seed()
>>> from profiles.models import Profile
>>> Profile.objects.count()
# Should print: 2026
>>> Profile.objects.first().name
# Should print: a name in lowercase
```

**Expected output:**
```
2026  # Total profiles seeded
```

---

## FIX #2: ERROR RESPONSE ENVELOPE (PRIORITY: 🔴 CRITICAL)

**Impact:** Fixes pagination and validation tests

### Problem
When pagination fails, the error response is malformed:

```python
# Current (WRONG)
result, meta = paginate(qs, page, limit)
if result is None:
    return error(meta, 422)  # meta is STRING: "Invalid query parameters"
    # Response: {"status": "error", "message": "Invalid query parameters"} ✓
    # But status is 422 ✗
```

The error format itself is correct, but:
1. Using 422 instead of 400
2. Pagination error handling is fragile

### Solution: Refactor Pagination

**File: `profiles/core/pagination.py`**

```python
from typing import Tuple, Dict, Any
from django.db.models import QuerySet

class PaginationError(Exception):
    """Raised when pagination parameters are invalid"""
    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


def paginate(
    qs: QuerySet,
    page: int | str,
    limit: int | str
) -> Tuple[QuerySet, Dict[str, Any]]:
    """
    Paginate a queryset with validation.
    
    Args:
        qs: Django QuerySet
        page: Page number (1-indexed)
        limit: Items per page
    
    Returns:
        (sliced_queryset, metadata_dict)
    
    Raises:
        PaginationError: If page or limit invalid
    """
    try:
        page = int(page)
        limit = int(limit)
    except (TypeError, ValueError):
        raise PaginationError("page and limit must be integers")
    
    if page < 1:
        raise PaginationError("page must be >= 1")
    if limit < 1:
        raise PaginationError("limit must be >= 1")
    
    # Cap limit to 50
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
```

### Update Views to Handle Error

**File: `profiles/views.py`** (Add this import at top)

```python
from profiles.core.pagination import paginate, PaginationError
```

**Update both endpoints:**

```python
def get_profiles(request):
    ensure_seed()
    qs = Profile.objects.all()
    
    # ... filtering and sorting code stays same ...
    
    # PAGINATION (NEW ERROR HANDLING)
    try:
        page = request.GET.get("page", 1)
        limit = request.GET.get("limit", 10)
        result, meta = paginate(qs, page, limit)
    except PaginationError as e:
        return error(e.message, 400)  # ✅ Use 400 for bad request
    
    data = [serialize(p) for p in result]
    return success(data, meta)


def search_profiles(request):
    ensure_seed()
    
    q = request.GET.get("q", "").lower()
    
    if not q:
        return error("Missing or empty parameter", 400)
    
    # ... parsing code stays same ...
    
    # PAGINATION (SAME ERROR HANDLING)
    try:
        page = request.GET.get("page", 1)
        limit = request.GET.get("limit", 10)
        result, meta = paginate(qs, page, limit)
    except PaginationError as e:
        return error(e.message, 400)  # ✅ Use 400
    
    data = [serialize(p) for p in result]
    return success(data, meta)
```

---

## FIX #3: HTTP STATUS CODES (PRIORITY: 🟠 HIGH)

**Impact:** Fixes query_validation test

### Problem
Invalid parameters return 422, should return 400

### Solution

**File: `profiles/views.py`**

Change these lines in `get_profiles()`:

```python
# BEFORE (WRONG)
if sort_by not in allowed:
    return error("Invalid query parameters", 422)  # ❌

if order not in ["asc", "desc"]:
    return error("Invalid query parameters", 422)  # ❌

# AFTER (CORRECT)
if sort_by not in allowed:
    allowed_str = ", ".join(allowed)
    return error(f"sort_by must be one of: {allowed_str}", 400)  # ✅

if order not in ["asc", "desc"]:
    return error("order must be 'asc' or 'desc'", 400)  # ✅
```

Also in `get_profiles()` filter validation:

```python
# BEFORE (WRONG)
if request.GET.get("min_age") and min_age is None:
    return error("Invalid query parameters", 422)

# AFTER (CORRECT)
if request.GET.get("min_age") and min_age is None:
    return error("min_age must be an integer", 400)
```

Do the same for: `max_age`, `min_gender_probability`, `min_country_probability`

---

## FIX #4: SEARCH ENDPOINT ERROR (PRIORITY: 🟠 HIGH)

**File: `profiles/views.py`**

```python
# BEFORE (WRONG)
if not parsed:
    return error("Unable to interpret query", 422)  # ❌ Should be 400

# AFTER (CORRECT)
if not parsed:
    return error("Unable to interpret query", 400)  # ✅
```

---

## VERIFICATION CHECKLIST

After implementing these fixes, test each one:

```bash
# Test 1: Seed data exists
curl "http://localhost:8000/api/profiles?page=1&limit=5"
# Should return 5 profiles in data array

# Test 2: Pagination limit capped
curl "http://localhost:8000/api/profiles?limit=100"
# Response should have "limit": 50 (capped)

# Test 3: Invalid sort_by returns 400
curl "http://localhost:8000/api/profiles?sort_by=invalid"
# Should return 400, not 422

# Test 4: Invalid page returns 400
curl "http://localhost:8000/api/profiles?page=abc"
# Should return 400 with error message

# Test 5: Search invalid returns 400
curl "http://localhost:8000/api/profiles/search?q=xyz123!@#"
# Should return 400 (if sanitization added)
# Or 422 if no sanitization (be consistent)

# Test 6: Combined filters work
curl "http://localhost:8000/api/profiles?gender=male&country_id=NG&min_age=25&sort_by=age&order=desc&page=1&limit=10"
# Should return filtered results

# Test 7: Search works
curl "http://localhost:8000/api/profiles/search?q=young+males+from+nigeria"
# Should return results matching query
```

---

## EXPECTED TEST RESULTS AFTER FIXES

```
✓ filtering_logic: 20/20 pts          (seed data + correct filters)
✓ combined_filters: 15/15 pts         (multiple filters working)
✓ sorting: 10/10 pts                  (correct sort_by + order)
✓ pagination: 15/15 pts               (correct envelope + limit cap)
✓ natural_language_parsing: 20/20 pts (seed data + parser works)
✓ query_validation: 5/5 pts           (correct error codes)
✓ readme_explanation: 10/10 pts       (already passing)
? performance: 0-5 pts                (depends on implementation)

TOTAL: 95-100/100 pts ✓ PASS
```

---

## NEXT: ENTERPRISE IMPROVEMENTS (Optional but Recommended)

Once you hit 75+, consider adding:

1. **Database Indexes** (1 hour)
   - Add `db_index=True` to filtered fields
   - Performance improvement for 2026+ profiles

2. **Constants File** (30 minutes)
   - Centralize magic strings
   - Makes code maintainable

3. **Tests** (1-2 hours)
   - Unit tests for validators
   - Integration tests for endpoints
   - Fixture-based test data

4. **Documentation** (30 minutes)
   - Type hints on all functions
   - Docstrings with examples

---

## IMPLEMENTATION ORDER

**Execute in this sequence:**

1. ✅ Obtain seed.json (2026 profiles)
2. ✅ Refactor pagination.py (add PaginationError)
3. ✅ Update views.py error handling
4. ✅ Change HTTP status codes (422 → 400)
5. ✅ Add input validation with better messages
6. ✅ Test all endpoints
7. ✅ Deploy to Vercel
8. ✅ Run /submit in Slack

---

## ESTIMATED TIME

- **Seed data:** 15 minutes (if you have the file)
- **Pagination refactor:** 30 minutes
- **Status code fixes:** 15 minutes
- **Error message improvements:** 15 minutes
- **Testing:** 20 minutes
- **Deployment:** 10 minutes

**Total: ~1.5-2 hours**

---

## DO NOT CHANGE

These are working correctly; don't modify:

✅ `models.py` - Schema is correct
✅ `urls.py` - Routes are correct
✅ `serializers.py` - Format is correct
✅ `settings.py` - Configuration is correct
✅ `api/index.py` - WSGI entry point is correct
✅ Search parsing logic - Parser works correctly

---

## COMMON PITFALLS TO AVOID

1. ❌ Don't use 422 for client validation errors (use 400)
2. ❌ Don't return dicts when function expects strings
3. ❌ Don't hardcode status codes in views (use constants)
4. ❌ Don't forget to clear Django cache between deployments
5. ❌ Don't test locally without seed data

---

## KEY INSIGHT

The grading script is looking for:

```python
# Correct response format
{
    "status": "success",  # or "error"
    "page": 1,
    "limit": 10,
    "total": 2026,
    "data": [...]
}

# Correct error format
{
    "status": "error",
    "message": "descriptive message"
}

# Correct status codes
200 - Success
400 - Client error (bad parameters)
500 - Server error
```

Anything else will fail.

---

**End of Implementation Guide**

*Follow this guide exactly to move from 10 → 75+ points. Enterprise improvements can come after.*
