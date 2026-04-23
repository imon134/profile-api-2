"""
Profile model for demographic intelligence data.
Represents individual demographic profiles with confidence scores.
"""

from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from profiles.utils import uuid7


class Profile(models.Model):
    """
    Demographic profile with validated data and confidence scores.

    Attributes:
        id: UUID v7 primary key (time-based, sortable)
        name: Unique profile name (stored lowercase)
        gender: 'male' or 'female' with confidence score
        age: Integer age with age_group classification
        country: ISO country code and name with confidence
        created_at: Creation timestamp (UTC)
    """

    # Primary Key
    id = models.UUIDField(
        primary_key=True,
        default=uuid7,
        editable=False,
        help_text="UUID v7 primary key (time-based, sortable)",
    )

    # Name
    name = models.CharField(
        max_length=255,
        unique=True,
        db_index=True,
        help_text="Full name (stored lowercase for consistency)",
    )

    # Gender
    gender = models.CharField(
        max_length=10,
        db_index=True,
        choices=[
            ("male", "Male"),
            ("female", "Female"),
        ],
        help_text="Gender: male or female",
    )

    gender_probability = models.FloatField(
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)],
        help_text="Confidence score for gender (0.0-1.0)",
    )

    # Age
    age = models.IntegerField(
        db_index=True,
        validators=[MinValueValidator(0), MaxValueValidator(150)],
        help_text="Exact age in years",
    )

    age_group = models.CharField(
        max_length=20,
        db_index=True,
        choices=[
            ("child", "Child (0-12)"),
            ("teenager", "Teenager (13-19)"),
            ("adult", "Adult (20-64)"),
            ("senior", "Senior (65+)"),
        ],
        help_text="Age group classification",
    )

    # Country
    country_id = models.CharField(
        max_length=2,
        db_index=True,
        help_text="ISO 3166-1 alpha-2 country code (e.g., NG, KE, GH)",
    )

    country_name = models.CharField(
        max_length=100,
        help_text="Full country name",
    )

    country_probability = models.FloatField(
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)],
        help_text="Confidence score for country (0.0-1.0)",
    )

    # Timestamps
    created_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
        help_text="Record creation timestamp (UTC)",
    )

    class Meta:
        verbose_name = "Profile"
        verbose_name_plural = "Profiles"
        ordering = ["-created_at"]
        indexes = [
            # Single field indexes for frequent filters
            models.Index(fields=["gender", "created_at"]),
            models.Index(fields=["age_group", "age"]),
            models.Index(fields=["country_id", "created_at"]),
            # Composite indexes for common query combinations
            models.Index(fields=["gender", "country_id"]),
            models.Index(fields=["age_group", "country_id"]),
        ]

    def __str__(self) -> str:
        """String representation of profile."""
        return f"{self.name} ({self.age}, {self.country_name})"

    def __repr__(self) -> str:
        """Developer-friendly representation."""
        return f"<Profile: {self.name} (id={self.id}, age={self.age}, country={self.country_id})>"

    @property
    def is_valid(self) -> bool:
        """
        Check if profile data is valid.

        Returns:
            True if all constraints are met
        """
        return (
            self.gender in ["male", "female"]
            and 0 <= self.gender_probability <= 1.0
            and 0 <= self.age <= 150
            and self.age_group in ["child", "teenager", "adult", "senior"]
            and len(self.country_id) == 2
            and 0 <= self.country_probability <= 1.0
        )