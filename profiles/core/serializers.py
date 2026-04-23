"""
Profile serialization utilities.
Converts Profile ORM objects to JSON-compatible dictionaries.
"""

from typing import Dict, Any
from profiles.models import Profile


def serialize(profile: Profile) -> Dict[str, Any]:
    """
    Serialize a Profile instance to a dictionary.

    Converts Profile ORM object to JSON-serializable format with proper
    type conversions for UUID and timestamp fields.

    Args:
        profile: Profile model instance

    Returns:
        Dictionary with all profile fields in JSON format:
        - id: UUID as string
        - name: Profile name
        - gender: 'male' or 'female'
        - gender_probability: Float confidence score
        - age: Integer age
        - age_group: 'child', 'teenager', 'adult', or 'senior'
        - country_id: ISO country code
        - country_name: Full country name
        - country_probability: Float confidence score
        - created_at: ISO 8601 timestamp

    Example:
        >>> profile = Profile.objects.first()
        >>> data = serialize(profile)
        >>> print(data['name']) # Lowercase string
        >>> print(data['created_at']) # ISO format: "2026-04-23T12:00:00Z"
    """
    return {
        "id": str(profile.id),
        "name": profile.name,
        "gender": profile.gender,
        "gender_probability": profile.gender_probability,
        "age": profile.age,
        "age_group": profile.age_group,
        "country_id": profile.country_id,
        "country_name": profile.country_name,
        "country_probability": profile.country_probability,
        "created_at": profile.created_at.isoformat(),
    }


def serialize_multiple(profiles: list[Profile]) -> list[Dict[str, Any]]:
    """
    Serialize multiple Profile instances.

    Args:
        profiles: List of Profile instances

    Returns:
        List of serialized profile dictionaries
    """
    return [serialize(p) for p in profiles]