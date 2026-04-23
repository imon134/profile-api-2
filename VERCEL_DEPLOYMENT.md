# Vercel Deployment Guide

This guide ensures the API runs properly on Vercel's serverless platform.

## ✅ Current Vercel Configuration

### vercel.json
```json
{
  "builds": [
    { "src": "api/index.py", "use": "@vercel/python" }
  ],
  "routes": [
    { "src": "/(.*)", "dest": "api/index.py" }
  ]
}
```

**What this does:**
- Builds the Python runtime using `@vercel/python`
- Routes all requests to the Django WSGI app in `api/index.py`

### api/index.py (WSGI Entry Point)
```python
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "profile_project.settings")
from django.core.wsgi import get_wsgi_application
app = get_wsgi_application()
```

This is the entry point for Vercel's serverless functions.

---

## 🔧 Required Vercel Environment Variables

Set these in Vercel Project Settings → Environment Variables:

### 1. **DATABASE_URL** (REQUIRED for production)

For PostgreSQL database (recommended for Vercel):
```
postgresql://user:password@host:5432/database_name
```

Or use Neon (PostgreSQL hosting):
```
postgresql://user:password@ep-xxxxx.region.neon.tech/dbname
```

**Why PostgreSQL?**
- SQLite doesn't work on Vercel (ephemeral filesystem)
- PostgreSQL persists across deployments
- Remote database accessible from serverless functions

### 2. **SECRET_KEY** (REQUIRED for production security)

Generate a secure key:
```bash
python3 -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

Set in Vercel:
```
sk-...  (your generated key)
```

### 3. **DJANGO_SETTINGS_MODULE** (Already configured)

Already set in `api/index.py`, but if you need to override:
```
profile_project.settings
```

---

## 📋 Pre-Deployment Checklist

### Local Testing (Before Pushing)

```bash
# 1. Verify requirements are installed
pip install -r requirements.txt

# 2. Run migrations locally
/usr/bin/python3 manage.py migrate

# 3. Run tests
/usr/bin/python3 manage.py test

# 4. Test API locally
/usr/bin/python3 manage.py runserver
# Test: http://127.0.0.1:8000/api/profiles
```

### Git Repository

```bash
# 1. Ensure seed.json is in git
git add data/seed.json
git commit -m "Add seed data"

# 2. Verify vercel.json is in git
git add vercel.json
git commit -m "Add Vercel config"

# 3. Push to GitHub
git push origin main
```

### Vercel Project Setup

1. **Connect GitHub**
   - Go to https://vercel.com
   - Click "New Project"
   - Import your GitHub repository
   - Select: `imon134/profile-api-2`

2. **Configure Build Settings**
   - Framework: "Other"
   - Build Command: (leave empty)
   - Output Directory: (leave empty)
   - Install Command: `pip install -r requirements.txt`

3. **Set Environment Variables**
   - Click "Environment Variables"
   - Add:
     - `DATABASE_URL`: Your PostgreSQL connection string
     - `SECRET_KEY`: Your Django secret key
   - Apply to all environments (Production, Preview, Development)

4. **Deploy**
   - Click "Deploy"
   - Wait for build to complete
   - Copy the deployment URL (e.g., `https://profile-api-2-xxxxx.vercel.app`)

---

## 🚀 Post-Deployment Setup

### Run Migrations on Vercel

**Option 1: Using Vercel CLI (Recommended)**

```bash
# 1. Install Vercel CLI
npm i -g vercel

# 2. Connect to Vercel project
vercel login

# 3. Pull environment variables
vercel env pull

# 4. Run migrations
export $(cat .env.local | xargs)
/usr/bin/python3 manage.py migrate

# 5. Seed database (if needed)
/usr/bin/python3 manage.py seed_profiles
```

**Option 2: Manual via Vercel Dashboard**

1. Go to Vercel Dashboard → Project
2. Click "Settings" → "Environment Variables"
3. Copy the DATABASE_URL value
4. Run locally:
   ```bash
   export DATABASE_URL="your_vercel_db_url"
   /usr/bin/python3 manage.py migrate
   /usr/bin/python3 manage.py seed_profiles
   ```

### Verify Deployment

Test the live API:

```bash
# Test basic endpoint
curl https://your-project.vercel.app/api/profiles

# Test with filters
curl "https://your-project.vercel.app/api/profiles?gender=male&page=1&limit=10"

# Test search endpoint
curl "https://your-project.vercel.app/api/profiles/search?q=young+males+from+nigeria"

# Test OpenAPI/Swagger
curl https://your-project.vercel.app/api/docs/
```

---

## ⚠️ Common Vercel Issues & Fixes

### Issue 1: 500 Error on First Request
**Cause:** Migrations not applied or database not connected

**Fix:**
```bash
# Run migrations before accessing endpoints
export DATABASE_URL="your_postgres_url"
/usr/bin/python3 manage.py migrate
```

### Issue 2: Database Connection Error
**Cause:** DATABASE_URL not set or incorrect

**Fix:**
1. Verify DATABASE_URL in Vercel Environment Variables
2. Test connection locally:
   ```bash
   python3 -c "import dj_database_url; print(dj_database_url.config())"
   ```

### Issue 3: Static Files Not Found (404)
**Not applicable** - This is an API-only project, no static files needed

### Issue 4: CORS Errors
**Already configured** - `CORS_ALLOW_ALL_ORIGINS = True` in settings.py

### Issue 5: Seed Data Not Found
**Cause:** seed.json not in repository

**Fix:**
```bash
# Ensure seed.json is committed
git add data/seed.json
git commit -m "Add seed data"
git push origin main
```

---

## 📊 Monitoring on Vercel

### Check Deployment Logs

1. Go to Vercel Dashboard → Project → Deployments
2. Click the latest deployment
3. View "Build Logs" and "Function Logs"
4. Look for errors in the logs

### Common Log Messages

```
✓ Build completed              → Success
✓ Function initialized         → Ready to serve
ERROR in get_wsgi_application  → Django config issue
Database error                 → Connection issue
```

---

## 🔐 Security Checklist

- ✅ DEBUG = False in settings.py
- ✅ SECRET_KEY not in code (uses env var)
- ✅ ALLOWED_HOSTS = ["*"] (Vercel requires this)
- ✅ CORS configured (needed for grading)
- ✅ Database credentials in env vars (not in code)
- ✅ No sensitive data in git repository

---

## 💡 Vercel Performance Tips

1. **Cold Starts**: First request might take 2-3 seconds (normal for serverless)
2. **Database Pool**: Use PostgreSQL connection pooling for better performance
3. **Caching**: Vercel caches static content; this is an API-only project
4. **Request Timeout**: Vercel has 60s timeout for Hobby plan, 900s for Pro
5. **Memory**: Vercel provides 3GB for Python functions

---

## 📝 Final Deployment Checklist

- [ ] All tests passing locally (`pytest` or `python manage.py test`)
- [ ] seed.json (2026 profiles) in repository
- [ ] vercel.json present and correct
- [ ] api/index.py present and correct
- [ ] requirements.txt updated
- [ ] GitHub repository pushed (latest commit)
- [ ] Vercel project created and connected to GitHub
- [ ] DATABASE_URL environment variable set on Vercel
- [ ] SECRET_KEY environment variable set on Vercel
- [ ] Migrations applied to Vercel database
- [ ] Seed data loaded to Vercel database
- [ ] Endpoints tested and working
- [ ] API URL ready for submission

---

## 🎯 Submission URLs

Once deployed and verified:

1. **API Base URL:**
   ```
   https://your-project-name.vercel.app/api/
   ```

2. **GitHub Repository:**
   ```
   https://github.com/imon134/profile-api-2
   ```

3. **Test Endpoints:**
   - `/api/profiles` - Get all profiles with filters
   - `/api/profiles/search?q=young+males+from+nigeria` - Natural language search
   - `/api/docs/` - OpenAPI documentation
   - `/api/schema/` - OpenAPI schema

---

## 🆘 Support & Debugging

If you encounter issues on Vercel:

1. **Check Vercel Logs**: Dashboard → Deployments → Latest → Logs
2. **Test DATABASE_URL**: Verify PostgreSQL is reachable
3. **Run Migrations**: Manually apply migrations if needed
4. **Check Environment Variables**: Ensure all required vars are set
5. **Verify Repository**: Push all changes to GitHub

For more help: https://vercel.com/docs/frameworks/django

