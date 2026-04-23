#!/usr/bin/env python3
"""
Vercel startup verification script.
Run this to verify the deployment is configured correctly.
"""

import os
import sys
import json
from pathlib import Path

def check_environment():
    """Check environment variables and configuration."""
    print("🔍 Checking Environment Variables...")
    
    checks = {
        "SECRET_KEY": os.environ.get("SECRET_KEY", "NOT SET"),
        "DATABASE_URL": "SET" if os.environ.get("DATABASE_URL") else "NOT SET",
        "DJANGO_SETTINGS_MODULE": os.environ.get("DJANGO_SETTINGS_MODULE", "profile_project.settings"),
    }
    
    for key, value in checks.items():
        status = "✅" if value != "NOT SET" else "⚠️"
        print(f"{status} {key}: {value}")
    
    return "NOT SET" not in [v for k, v in checks.items() if k != "DJANGO_SETTINGS_MODULE"]

def check_files():
    """Check required files exist."""
    print("\n📁 Checking Required Files...")
    
    required_files = [
        "manage.py",
        "requirements.txt",
        "vercel.json",
        "api/index.py",
        "profile_project/settings.py",
        "profile_project/urls.py",
        "profile_project/wsgi.py",
        "profiles/models.py",
        "profiles/views.py",
        "profiles/urls.py",
        "profiles/core/constants.py",
        "profiles/core/errors.py",
        "profiles/core/validators.py",
        "profiles/core/pagination.py",
        "profiles/core/serializers.py",
        "profiles/core/search_parser.py",
        "profiles/core/seed.py",
        "data/seed.json",
    ]
    
    all_exist = True
    for file_path in required_files:
        exists = Path(file_path).exists()
        status = "✅" if exists else "❌"
        print(f"{status} {file_path}")
        if not exists:
            all_exist = False
    
    return all_exist

def check_django_setup():
    """Check Django setup."""
    print("\n⚙️ Checking Django Setup...")
    
    try:
        os.environ.setdefault("DJANGO_SETTINGS_MODULE", "profile_project.settings")
        import django
        django.setup()
        print("✅ Django setup successful")
        
        # Check database connection
        from django.db import connections
        conn = connections['default']
        cursor = conn.cursor()
        print(f"✅ Database connected: {conn.settings_dict.get('ENGINE', 'Unknown')}")
        
        # Check profile count
        from profiles.models import Profile
        count = Profile.objects.count()
        print(f"✅ Profiles in database: {count}")
        
        if count < 2026:
            print(f"⚠️ WARNING: Only {count} profiles (expected 2026). Run: python manage.py seed_profiles")
        
        return True
    except Exception as e:
        print(f"❌ Django setup failed: {e}")
        return False

def check_endpoints():
    """Check API endpoints are configured."""
    print("\n🔗 Checking API Endpoints...")
    
    try:
        from django.urls import get_resolver
        resolver = get_resolver()
        
        patterns = []
        for pattern in resolver.url_patterns:
            patterns.append(str(pattern.pattern))
        
        expected = [
            "api/profiles",
            "api/profiles/search",
        ]
        
        for endpoint in expected:
            found = any(endpoint in p for p in patterns)
            status = "✅" if found else "❌"
            print(f"{status} {endpoint}")
        
        return True
    except Exception as e:
        print(f"❌ Endpoint check failed: {e}")
        return False

def main():
    """Run all checks."""
    print("=" * 60)
    print("🚀 Vercel Deployment Verification")
    print("=" * 60)
    
    env_ok = check_environment()
    files_ok = check_files()
    django_ok = check_django_setup()
    endpoints_ok = check_endpoints()
    
    print("\n" + "=" * 60)
    print("📊 Summary")
    print("=" * 60)
    
    checks = {
        "Environment Variables": env_ok,
        "Required Files": files_ok,
        "Django Setup": django_ok,
        "API Endpoints": endpoints_ok,
    }
    
    all_passed = all(checks.values())
    
    for check_name, passed in checks.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {check_name}")
    
    print("=" * 60)
    
    if all_passed:
        print("✅ All checks passed! Ready for Vercel deployment.")
        return 0
    else:
        print("❌ Some checks failed. See above for details.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
