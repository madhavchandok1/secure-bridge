from slowapi import Limiter
from slowapi.util import get_remote_address

from app.config import settings

limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[
        "100/minute"
    ]
)

AUTH_LOGIN_LIMIT = settings.RATE_LIMIT_LOGIN
AUTH_REGISTER_LIMIT = settings.RATE_LIMIT_REGISTER
