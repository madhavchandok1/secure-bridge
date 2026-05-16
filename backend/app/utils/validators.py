import re

from app.core.constants import RESERVED_SLUGS

# Regular expression for validating URL-friendly slugs.
# - ^[a-z0-9]+   : Must start with one or more alphanumeric characters.
# - (?:-[a-z0-9]+)*$: Can contain subsequent alphanumeric segments separated by a single hyphen.
# This prevents leading, trailing, or consecutive hyphens (e.g., "-my-slug", "slug--name").
SLUG_REGEX = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


def validate_slug(slug: str) -> str:
    """
    Validates and sanitizes an organization slug against structural and safety rules.

    The validation ensures the slug is URL-safe, adheres to length boundaries, 
    matches the required kebab-case format, and does not conflict with protected system routes.

    Args:
        slug (str): The raw input slug string from the user or API request.

    Returns:
        str: The sanitized, lowercase, and stripped slug string.

    Raises:
        ValueError: If the slug violates length constraints, uses forbidden characters, 
                    contains invalid hyphen placements, or is a reserved keyword.
    """

    # Sanitize the input by removing surrounding whitespace and converting to lowercase
    slug = slug.strip().lower()

    # 1. Length Constraint Validation
    # Keeps slugs practical for URLs and database index constraints (matching your DB schema limit of 50).
    if len(slug) < 3 or len(slug) > 50:
        raise ValueError("Slug must be between 3 and 50 characters.")
    
    # 2. Security Check: Reserved Keywords
    # Prevents impersonation (e.g., 'admin', 'support') or breaking system-level routes.
    if slug in RESERVED_SLUGS:
        raise ValueError("Slug is reserved and cannot be used.")
    
    # 3. Format Validation: Regex Matching
    # Guarantees the slug contains only lowercase letters, numbers, and well-placed hyphens.
    if not SLUG_REGEX.fullmatch(slug):
        raise ValueError(
            "Slug must contain lowercase alphanumeric characters and single hyphens only, "
            "and cannot start or end with a hyphen."
        )
    
    return slug

def normalize_email(email: str) -> str:
    """
    Standardizes an email address to ensure consistency across the platform.

    Trims accidental whitespace and converts the address to lowercase. This prevents 
    duplicate registrations due to casing variations (e.g., 'User@Domain.com' vs 'user@domain.com').

    Args:
        email (str): The raw input email string.

    Returns:
        str: The fully normalized lowercase and stripped email address.
    """
    return email.strip().lower()