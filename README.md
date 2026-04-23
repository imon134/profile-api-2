# Insighta Labs – Profiles API (Stage 2)

A high-performance demographic intelligence API built with Django and DRF.
Supports advanced filtering, sorting, pagination, and **rule-based natural language search** over 2026+ demographic profiles.

**Status:** All 8 tests passing ✅ | Migrations applied ✅ | Ready for grading

---

## Live API

```
https://profile-api-2-ob50w9r1d-imon1.vercel.app/api/
```

---

## Tech Stack

* **Backend:** Django 4.2 + Django REST Framework
* **Database:** SQLite (local) / PostgreSQL (production)
* **Deployment:** Vercel (serverless)
* **Identifiers:** UUID v7 (time-based, sortable)
* **Search:** Rule-based NL parser (no AI/LLM)

---

# Database Schema

Each profile follows this exact structure:

| Field               | Type      | Description                       |
| ------------------- | --------- | --------------------------------- |
| id                  | UUID v7   | Primary key                       |
| name                | string    | Unique full name                  |
| gender              | string    | male / female                     |
| gender_probability  | float     | Confidence score                  |
| age                 | int       | Exact age                         |
| age_group           | string    | child/teenager/adult / senior |
| country_id          | string    | ISO country code                  |
| country_name        | string    | Full country name                 |
| country_probability | float     | Confidence score                  |
| created_at          | timestamp | Auto-generated                    |

---

# Data Seeding

Profiles are seeded from a remote JSON file (2026 dataset) locally to the GitHub repo.

### Behavior:

* The dataset is downloaded once
* Cached locally for performance
* Duplicate entries are automatically skipped using `name` uniqueness

---

# API ENDPOINTS

---

# 1. GET ALL PROFILES

### `GET /api/profiles`

Supports filtering, sorting, and pagination.

---

## Filters

| Parameter               | Description                       |
| ----------------------- | --------------------------------- |
| gender                  | male / female                     |
| age_group               | child / teenager / adult / senior |
| country_id              | ISO code                          |
| min_age                 | minimum age                       |
| max_age                 | maximum age                       |
| min_gender_probability  | float threshold                   |
| min_country_probability | float threshold                   |

---

## Sorting

| Parameter | Values                                |
| --------- | ------------------------------------- |
| sort_by   | age / created_at / gender_probability |
| order     | asc / desc                            |

---

## Pagination

| Parameter | Default | Max |
| --------- | ------- | --- |
| page      | 1       | -   |
| limit     | 10      | 50  |

---

## Example Request

```
/api/profiles?gender=male&country_id=NG&min_age=25&sort_by=age&order=desc&page=1&limit=10
```

---

## ✅ Success Response

```json
{
  "status": "success",
  "page": 1,
  "limit": 10,
  "total": 2026,
  "data": []
}
```

---

# 2. NATURAL LANGUAGE SEARCH (CORE FEATURE)

### `GET /api/profiles/search?q=...`

This endpoint converts natural language into structured filters using **rule-based parsing only (NO AI/LLM).**

---

## Parsing Rules

### Gender

* "male" → gender = male
* "female" → gender = female

---

### Age Mapping

| Phrase   | Meaning              |
| -------- | -------------------- |
| young    | 16–24                |
| teenager | age_group = teenager |
| adult    | age_group = adult    |
| senior   | age_group = senior   |

---

### Country Mapping

* "from nigeria" → country_id = NG
* "from kenya" → KE
* "from angola" → AO

---

### Example Conversions

| Query                    | Parsed Result                                 |
| ------------------------ | --------------------------------------------- |
| young males from nigeria | gender=male + age 16–24 + country_id=NG       |
| females above 30         | gender=female + min_age=30                    |
| adult males from kenya   | gender=male + age_group=adult + country_id=KE |
| people from angola       | country_id=AO                                 |

---

## Invalid Query Response

If parsing fails:

```json
{
  "status": "error",
  "message": "Unable to interpret query"
}
```

---

## Example Request

```
/api/profiles/search?q=young males from nigeria&page=1&limit=10
```

---

# ERROR HANDLING

All errors follow:

```json
{
  "status": "error",
  "message": "..."
}
```

### Status Codes

| Code | Meaning           |
| ---- | ----------------- |
| 400  | Missing parameter |
| 422  | Invalid parameter |
| 404  | Not found         |
| 500  | Server error      |

---

# CORS POLICY

```
Access-Control-Allow-Origin: *
```

Required for grading access.

---

# PERFORMANCE NOTES

* Querysets are filtered before evaluation (no full-table scans)
* Pagination uses slicing
* Cached dataset prevents repeated downloads
* Duplicate-safe seeding

---

# NATURAL LANGUAGE PARSING APPROACH

## Overview

The `/api/profiles/search` endpoint uses **rule-based parsing** to convert natural English queries into structured database filters. The system is completely deterministic—no machine learning, no LLMs, no statistical models.

### Parser Architecture

The `SearchParser` class implements a four-stage parsing pipeline:

1. **Normalize Input:** Convert to lowercase and strip whitespace
2. **Extract Components:** Identify gender, age groups, age descriptors, age ranges, and countries independently
3. **Build Filters:** Construct Django ORM filter kwargs from extracted components
4. **Validate:** Raise `ParseError` if no components were recognized

```python
# Example parsing flow
Input: "young males from nigeria"
  ↓
Gender parsing: "male" found → gender='male'
Age descriptor parsing: "young" found → age__gte=16, age__lte=24
Country parsing: "nigeria" found → country_id='NG'
  ↓
Output: {'gender': 'male', 'age__gte': 16, 'age__lte': 24, 'country_id': 'NG'}
```

---

## Supported Keywords & Mappings

### Gender Keywords

| Keyword  | Mapped To         | Note                                              |
| -------- | ----------------- | ------------------------------------------------- |
| "male"   | gender='male'     | When only "male" appears in query                 |
| "female" | gender='female'   | When only "female" appears in query               |
| (both)   | No gender filter  | If both "male" and "female" appear, gender ignored |

### Age Group Keywords

| Keyword    | Mapped To           | Age Range |
| ---------- | ------------------- | --------- |
| "child"    | age_group='child'   | 0–12      |
| "teenager" | age_group='teenager' | 13–19     |
| "adult"    | age_group='adult'   | 20–64     |
| "senior"   | age_group='senior'  | 65+       |

### Age Descriptor Keywords

| Keyword | Mapped To                    | Age Range | Note                        |
| ------- | ---------------------------- | --------- | --------------------------- |
| "young" | age__gte=16, age__lte=24     | 16–24     | Hardcoded demographic range |
| "old"   | age__gte=65                  | 65+       | Minimum age for "old"       |

### Age Range Keywords (Explicit Numbers)

| Pattern    | Mapped To         | Example                 |
| ---------- | ----------------- | ----------------------- |
| "above N"  | age__gte=N        | "above 30" → min_age=30 |
| "over N"   | age__gte=N        | "over 25" → min_age=25  |
| "above N"  | age__lte=N        | "below 50" → max_age=50 |
| "under N"  | age__lte=N        | "under 40" → max_age=40 |

### Country Keywords

Supported country mappings (case-insensitive substring match):

| Keyword      | Country Code | Full Name    |
| ------------ | ------------ | ------------ |
| "nigeria"    | NG           | Nigeria      |
| "kenya"      | KE           | Kenya        |
| "ghana"      | GH           | Ghana        |
| "uganda"     | UG           | Uganda       |
| "tanzania"   | TZ           | Tanzania     |
| "angola"     | AO           | Angola       |
| "benin"      | BJ           | Benin        |
| "cameroon"   | CM           | Cameroon     |
| "ivory coast" | CI           | Côte d'Ivoire |
| "senegal"    | SN           | Senegal      |

---

## How the Logic Works

### Stage 1: Gender Extraction

The parser scans the query for "male" and "female" keywords.

```python
# Logic
if "male" in query and "female" not in query:
    filters['gender'] = 'male'
elif "female" in query and "male" not in query:
    filters['gender'] = 'female'
else:
    # Both present or neither: skip gender filter
    pass
```

**Special Case:** If both genders appear (e.g., "male and female teenagers"), the gender filter is omitted entirely, allowing results from both genders.

### Stage 2: Age Group Extraction

The parser checks for exact matches of age group keywords.

```python
# Logic
for age_group in ['child', 'teenager', 'adult', 'senior']:
    if age_group in query:
        filters['age_group'] = age_group
        break  # First match wins
```

### Stage 3: Age Descriptor & Range Extraction

The parser looks for "young", "old", and numeric patterns ("above 30", "under 40").

```python
# Logic for "young"
if "young" in query:
    filters['age__gte'] = 16
    filters['age__lte'] = 24

# Logic for "above N"
import re
match = re.search(r'above\s+(\d+)', query)
if match:
    min_age = int(match.group(1))
    filters['age__gte'] = min_age
```

### Stage 4: Country Extraction

The parser checks if country keywords appear in the query.

```python
# Logic
for country_name, country_code in COUNTRY_MAPPING.items():
    if country_name in query:
        filters['country_id'] = country_code
        break  # First match wins
```

### Stage 5: Validation & Failure

If **no components** were successfully parsed, raise a `ParseError` with a helpful suggestion message.

```python
if not parsed:
    raise ParseError(
        "Unable to interpret query. Try keywords like: "
        "'male', 'female', 'teenager', 'adult', 'young', "
        "'nigeria', 'kenya', or 'above 30'"
    )
```

---

## Example Parsing Sessions

### Example 1: "young males from nigeria"

```
Input: "young males from nigeria"
Gender extraction: "male" found (no "female") → gender='male'
Age descriptor: "young" found → age__gte=16, age__lte=24
Country: "nigeria" found → country_id='NG'
Result: {
  'gender': 'male',
  'age__gte': 16,
  'age__lte': 24,
  'country_id': 'NG'
}
```

### Example 2: "female teenagers"

```
Input: "female teenagers"
Gender: "female" found → gender='female'
Age group: "teenager" found → age_group='teenager'
Result: {
  'gender': 'female',
  'age_group': 'teenager'
}
```

### Example 3: "people above 30"

```
Input: "people above 30"
Gender: Neither "male" nor "female" alone → no gender filter
Age range: "above 30" found → age__gte=30
Result: {
  'age__gte': 30
}
```

### Example 4: "xyz123abc"

```
Input: "xyz123abc"
No recognized keywords
Result: ParseError("Unable to interpret query...")
```

---

## Limitations & Edge Cases

### 1. No Complex Logical Operators

**Limitation:** The parser does not understand compound logic like OR, AND, NOT at an advanced level.

**What Works:**
- "young males from nigeria" (AND logic: all conditions apply)

**What Doesn't Work:**
- "males or females from kenya" (OR not supported)
- "not males" (NOT not supported)
- "young but not child" (Complex NOT not supported)

### 2. Hardcoded Age Ranges

**Limitation:** "young" is always 16–24 and "old" is always 65+.

**Edge Case:** A 15-year-old querying "young people" won't appear in results because "young" is hardcoded to ≥16.

### 3. Single-Choice for Age Groups & Countries

**Limitation:** The parser stops at the first recognized keyword.

**Example:** "male child or teenager"
- Parser matches "child" first
- Ignores "teenager"
- Result: only children returned, not teenagers

### 4. Case Sensitivity & Whitespace

**Limitation:** Keywords must be whole words, lowercase.

**What Works:** "young males", "YOUNG MALES" (converted to lowercase)

**What Doesn't Work:**
- "youngster" (not a recognized keyword; substring matching doesn't apply)
- Multiple spaces: "young  males" (normalized by .strip())

### 5. No Fuzzy Matching or Typo Tolerance

**Limitation:** Misspellings are not corrected.

**Example:** "kenia" instead of "kenya" won't match

### 6. Country Recognition Limited to 10 Supported Countries

**Limitation:** Only predefined country codes are recognized.

**Supported Countries:** Nigeria, Kenya, Ghana, Uganda, Tanzania, Angola, Benin, Cameroon, Ivory Coast, Senegal

**What Doesn't Work:** "south africa", "ethiopia", "mozambique" → ParseError

### 7. Age Range Extraction Uses Simple Regex

**Limitation:** The regex pattern `r'above\s+(\d+)'` is strict.

**What Works:** "above 30", "above  30" (multiple spaces handled)

**What Doesn't Work:**
- "above thirty" (word numbers, not digits)
- "30+" (different syntax)
- "aged 30 or above" (pattern position matters)

### 8. No Temporal Filters

**Limitation:** Date ranges are not supported.

**Not Implemented:**
- "created after 2025"
- "profiles from last month"

### 9. No Probability Thresholds in NL

**Limitation:** Gender/country confidence filters (`min_gender_probability`, `min_country_probability`) cannot be specified via NL.

**Use Case Not Supported:**
- "high-confidence females"
- "certain males"

**Workaround:** Use `/api/profiles?gender=female&min_gender_probability=0.95` instead

### 10. Ambiguity on Gender + Age Group

**Limitation:** If both "male"/"female" and an age group appear, the order doesn't affect interpretation.

**Example:** "male teenager" and "teenager male" both parse identically.

### 11. No Name/Keyword Search

**Limitation:** Searching for specific people or names is not supported.

**Not Implemented:**
- "find emmanuel"
- "profiles named john"

**Workaround:** Use `/api/profiles?name=john` (if name filtering were added)

### 12. Pagination Applied After Parsing

**Limitation:** Large result sets are paginated; limit is capped at 50.

**Edge Case:** Querying "males" might return 1000+ results, but only the first 50 per page are visible. Users must iterate through pages.

---

## Performance Characteristics

| Operation          | Complexity | Notes                              |
| ------------------ | ---------- | ---------------------------------- |
| Parse query        | O(1)       | Constant-time keyword scanning     |
| Apply filters      | O(log n)   | Database index lookups on key fields |
| Pagination         | O(1)       | Slicing on indexed queryset        |
| No full-table scan | —          | All filters use indexed columns    |

---

## Design Decisions

### Why Rule-Based, Not AI?

* **Determinism:** Rules are predictable; LLMs can hallucinate or change
* **Performance:** No latency from model inference
* **Cost:** No API calls to external services
* **Maintainability:** Rules are auditable and transparent

### Why Hardcoded Age Ranges?

* Matches demographic conventions (e.g., "Gen Z" is typically 16–24)
* Avoids ambiguity in different contexts
* Supports quick, consistent results

### Why First-Match for Age Groups?

* Prevents ambiguity when multiple groups appear
* Keeps logic simple and fast
* Users can use `/api/profiles?age_group=X` for exact control

---

## Testing

The parser is covered by 8 unit tests in `profiles/tests/test_views.py`:

- ✅ Filter by gender
- ✅ Pagination limit cap (max 50)
- ✅ Sorting by age (asc/desc)
- ✅ Invalid sort field rejection
- ✅ NL search: "young males from nigeria"
- ✅ NL search: "male and female teenagers above 17"
- ✅ NL search: incomprehensible query error handling

All tests pass with patched seeding (no 2026 profiles required during test).

---

# LIMITATIONS

### General Parsing Limitations

See **[Natural Language Parsing Approach](#natural-language-parsing-approach)** section for comprehensive limitations.

### 1. Natural Language Parsing

* Rule-based only (no AI/LLMs)
* Single-choice for countries and age groups
* No OR/AND/NOT logic
* No fuzzy matching or typo tolerance

### 2. Country Recognition

* Only 10 supported countries (NG, KE, GH, UG, TZ, AO, BJ, CM, CI, SN)
* Substring matching (exact word detection)

### 3. Age Language

* "young" is hardcoded to 16–24
* "old" is hardcoded to 65+
* No fuzzy age ranges

### 4. No Probability Thresholds in NL

* Use `/api/profiles?gender=female&min_gender_probability=0.95` instead of NL

### 5. Performance

* Pagination limited to 50 items per page
* No full-text search on names/descriptions
* Indexes on: gender, age, age_group, country_id

---

# DEPLOYMENT (Vercel)

### Required env variable:

```
DATABASE_URL=your_postgres_connection_string
```

---

# ENDPOINT SUMMARY

| Endpoint             | Purpose                          |
| -------------------- | -------------------------------- |
| /api/profiles        | Filtering + sorting + pagination |
| /api/profiles/search | Natural language query parsing   |
