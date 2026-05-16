from slowapi import Limiter
from slowapi.util import get_remote_address

from app.config import settings

# Initialize the Rate Limiter.
# key_func: Defines how to identify a unique user. Using 'get_remote_address' 
# identifies users by their IP address.
# default_limits: The fallback rate limit applied to any route that uses 
# the limiter but doesn't specify its own threshold.
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[
        "100/minute"
    ]
)

# Domain-specific rate limits pulled from global settings.
# These allow for granular control over sensitive endpoints like 
# Authentication to mitigate brute-force and credential-stuffing attempts.

# Limit for login attempts (e.g., "5/minute")
AUTH_LOGIN_LIMIT = settings.RATE_LIMIT_LOGIN

# Limit for new account registrations (e.g., "3/minute")
AUTH_REGISTER_LIMIT = settings.RATE_LIMIT_REGISTER
