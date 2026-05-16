"""
Schemas Package Entry Point.

This module centralizes and exports all Pydantic validation and serialization 
schemas used across the application API layer. This eliminates deeply nested 
imports in route definitions and provides a structured manifest of the 
application's data contracts.
"""

from app.schemas.auth import (
    MemberRegisterRequest, 
    MemberLoginRequest, 
    TokenResponse,
    AuthContext
)
from app.schemas.common import (
    DatabaseHealth, 
    SystemMetrics, 
    HealthResponse
)
from app.schemas.organization import (
    SetupOrganizationRequest, 
    SetupOrganizationResponse, 
    OrganizationResponse, 
    SlugAvailabilityResponse, 
    InviteKeyResponse
)
from app.schemas.user import (
    UserListResponse, 
    UserResponse, 
    UserUpdateRequest
)

# The __all__ tuple defines the explicit public boundary for the schemas layer.
# It controls what is exposed when a consumer uses 'from app.schemas import *'
# and guarantees a cleanly documented, flat namespace for the API routers.
__all__ = [
    # Infrastructure & Monitoring Contracts
    "DatabaseHealth",
    "SystemMetrics",
    "HealthResponse",
    
    # Organization Management Contracts
    "SetupOrganizationRequest",
    "OrganizationResponse",
    "SetupOrganizationResponse",
    "SlugAvailabilityResponse",
    "InviteKeyResponse",
    
    # Authentication & Session Contracts
    "MemberRegisterRequest",
    "MemberLoginRequest",
    "TokenResponse",
    "AuthContext",
    
    # User Profile & Management Contracts
    "UserListResponse",
    "UserResponse",
    "UserUpdateRequest",
]