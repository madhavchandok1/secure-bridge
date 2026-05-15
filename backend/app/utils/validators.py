import re

from app.core.constants import RESERVED_SLUGS

SLUG_REGEX = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


def validate_slug(slug: str) -> str:
    """
    Validate organization slug.
    """

    slug = slug.strip().lower()

    if len(slug) < 3 or len(slug) > 50:
        raise ValueError("Slug must be between 3 and 50 characters.")
    
    if slug in RESERVED_SLUGS:
        raise ValueError("Slug is reserved.")
    
    if not SLUG_REGEX.fullmatch(slug):
        raise ValueError(
            "Slug must contain lowercase letters, numbers, and hyphens only."
        )
    
    return slug

def normalize_email(email: str) -> str:
    return email.strip().lower()