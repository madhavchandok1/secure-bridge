from enum import Enum

class OrgRole(str, Enum):
    """
    Defines the authorization levels available within an organization.

    These roles determine the scope of permissions for a user:
    - OWNER: Full control over the organization, including billing and deletion.
    - ADMIN: Operational control, including member management and project settings.
    - MEMBER: Standard access to view and interact with shared resources.
    """

    # Highest privilege: Can manage all aspects of the organization and its members.
    OWNER = "owner"

    # Elevated privilege: Can manage members and configuration, but cannot delete the org.
    ADMIN = "admin"
    
    # Standard privilege: General access to organization data and collaborative tools.
    MEMBER = "member"