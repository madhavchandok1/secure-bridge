"""
Models Package Entry Point.

This module exports all database models to simplify imports throughout the 
application and ensure they are registered with the SQLAlchemy metadata 
for Alembic migrations.
"""

from app.models.organization import Organization
from app.models.user import User

# The __all__ variable defines the public interface of the module.
# It ensures that 'from app.models import *' only exposes the models 
# we want, while also helping linters and IDEs with autocompletion.
__all__ = [
    "Organization",
    "User"
]