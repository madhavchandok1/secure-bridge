"""
Repositories Package Entry Point.

This module centralizes and exports all domain-specific repository classes, 
providing a single, structured interface for data operations. It isolates 
higher-level service layers from direct module file paths.
"""

from app.repositories.organization_repository import OrganizationRepository
from app.repositories.user_repository import UserRepository

# The __all__ tuple defines the public namespace boundary for the repositories layer.
# This prevents internal helper utilities or parent classes (like BaseRepository) 
# from leaking into service layers during wildcard imports.
__all__ = [
    "OrganizationRepository",
    "UserRepository"
]