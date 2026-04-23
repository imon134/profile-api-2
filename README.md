# Insighta Labs – Profiles API

A high-performance demographic intelligence API built with Django and PostgreSQL (Neon).
It supports advanced filtering, sorting, pagination, and rule-based natural language querying over 2026 seeded profiles.

---

# Live API

Base URL:

```
https://profile-api-2-ob50w9r1d-imon1.vercel.app/
```

---

# Tech Stack

* Django (REST-style API)
* PostgreSQL (Neon DB)
* Vercel (serverless deployment)
* UUID v7 identifiers
* JSON-based dataset seeding

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

# LIMITATIONS

### 1. Natural Language Parsing

* Rule-based only
* No AI/LLMs used
* Cannot resolve complex nested logic

### 2. Country Recognition

* Only predefined mappings supported

### 3. Age Language

* "young" fixed to 16–24

### 4. No ML/NLP inference

* Fully deterministic logic only

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
