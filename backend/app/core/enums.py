from enum import Enum


class OrgRole(str, Enum):
    OWNER = "owner"
    ADMIN = "admin"
    MEMBER = "member"