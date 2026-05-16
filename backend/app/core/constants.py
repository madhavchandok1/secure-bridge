"""
Configuration for URL identifier restrictions.
This set defines 'slugs' that are protected and cannot be registered by users
to prevent routing conflicts and impersonation risks.
"""

# A collection of protected keywords that cannot be used as organization slugs.
# These are reserved to ensure that system-level routes (e.g., /admin, /api)
# remain accessible and to prevent users from creating deceptive URLs.

RESERVED_SLUGS = {
    # System Administration & Access
    "admin",
    "root",
    "system",
    "support",
    
    # Internal Infrastructure & Routing
    "api",
    "app",
    "auth",
    "status",
    
    # Common User Interface Routes
    "dashboard",
    "settings",
    "login",
    "signup",
}