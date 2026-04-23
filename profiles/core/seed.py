"""
Database seeding utilities.
Loads demographic profile data from JSON file into database.
Idempotent and safe for repeated execution.
"""

import json
from pathlib import Path
from typing import List
from django.conf import settings
from profiles.models import Profile
from profiles.core.logger import get_logger

logger = get_logger(__name__)


def ensure_seed() -> None:
    """
    Ensure database is seeded with profile data.

    Loads profiles from seed.json if not already in database.
    Idempotent: safe to call multiple times.

    Side effects:
        - Creates Profile records in database if missing
        - Logs seed operation results

    Raises:
        FileNotFoundError: If seed.json not found
        ValueError: If seed.json invalid or has insufficient records
        Exception: On database errors (re-raises)

    Example:
        >>> ensure_seed()
        >>> Profile.objects.count()
        2026
    """
    # Check if already seeded (idempotent)
    current_count = Profile.objects.count()
    if current_count >= 2026:
        logger.info(f"Database already seeded with {current_count} profiles")
        return

    logger.info("Starting database seeding...")

    try:
        # Load seed data
        seed_file = settings.BASE_DIR / "data" / "seed.json"
        logger.info(f"Loading seed data from {seed_file}")

        with open(seed_file, "r") as f:
            data = json.load(f)

        profiles_data = data.get("profiles", [])

        if not profiles_data:
            raise ValueError("seed.json contains no profiles")

        if len(profiles_data) < 2026:
            raise ValueError(
                f"seed.json has {len(profiles_data)} profiles, expected at least 2026"
            )

        # Create Profile objects
        profiles_to_create = []
        for p in profiles_data:
            profile = Profile(
                name=p["name"].strip().lower(),
                gender=p["gender"].lower(),
                gender_probability=float(p["gender_probability"]),
                age=int(p["age"]),
                age_group=p["age_group"].lower(),
                country_id=p["country_id"].upper(),
                country_name=p["country_name"],
                country_probability=float(p["country_probability"]),
            )
            profiles_to_create.append(profile)

        # Bulk create for performance
        Profile.objects.bulk_create(profiles_to_create, batch_size=500)

        final_count = Profile.objects.count()
        logger.info(f"Successfully seeded {final_count} profiles")

    except FileNotFoundError as e:
        logger.error(f"Seed file not found: {e}")
        raise

    except (ValueError, KeyError, TypeError) as e:
        logger.error(f"Invalid seed data format: {e}")
        raise

    except Exception as e:
        logger.error(f"Error during seeding: {e}", exc_info=True)
        raise


def get_seed_count() -> int:
    """
    Get current number of seeded profiles.

    Returns:
        Number of Profile records in database
    """
    return Profile.objects.count()


def clear_seed() -> int:
    """
    Clear all profiles from database.

    WARNING: Destructive operation. Use with caution.

    Returns:
        Number of profiles deleted

    Example:
        >>> clear_seed()
        2026
    """
    count, _ = Profile.objects.all().delete()
    logger.warning(f"Deleted {count} profiles from database")
    return count