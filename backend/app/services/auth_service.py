from datetime import UTC, datetime

from fastapi import HTTPException

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.enums import OrgRole
from app.core.security import (
    create_access_token, 
    decrypt_invite_key
)
from app.integrations.supabase_client import supabase
from app.models.user import User
from app.repositories import (
    OrganizationRepository, 
    UserRepository
)
from app.schemas import (
    TokenResponse, 
    MemberRegisterRequest, 
    MemberLoginRequest, 
    AuthContext
)
from app.utils.validators import normalize_email


class AuthService:
    """
    Business service layer orchestrating Authentication and Session Management.
    
    Acts as the single point of coordination between internal database states 
    (PostgreSQL repositories) and external cloud infrastructure components (Supabase Auth).
    """
    def __init__(self):
        """Initializes the service and couples its internal data access layers."""
        self.organization_repository = OrganizationRepository()
        self.user_repository = UserRepository()

    
    async def register_member(
        self,
        db: AsyncSession,
        data: MemberRegisterRequest,
    ) -> User:
        """
        Registers a new team member into an existing organization tenant workspace.

        Validates the organization's existence, verifies the tenant's unencrypted 
        invitation key, ensures email uniqueness, provisions an identity inside 
        Supabase Auth, and saves the matching profile record to the local database.

        Args:
            db (AsyncSession): The active asynchronous database unit-of-work transaction.
            data (MemberRegisterRequest): Validated onboarding request payload.

        Returns:
            User: The newly populated, persistent local User database entity.

        Raises:
            HTTPException (404): If the targeted organization slug does not exist.
            HTTPException (403): If the workspace invite key validation fails.
            HTTPException (409): If the identity is already registered locally or conflicts occur.
            HTTPException (500): If cloud provider provisioning anomalies arise.
        """

        # Tracking pointer used to execute compensatory deletion logic if downstream database operations fail
        supabase_user_id = None

        try:
            # 1. Locate the targeted tenant organization workspace
            organization = await self.organization_repository.get_by_slug(
                db=db,
                slug=data.org_slug,
            )

            if not organization:
                raise HTTPException(
                    status_code=404,
                    detail="Organization not found.",
                )

            actual_invite_key = decrypt_invite_key(
                encrypted_invite_key=organization.encrypted_invite_key
            )

            # 2. Cryptographically decrypt and verify the workspace registration token
            if actual_invite_key != data.invite_key:
                raise HTTPException(
                    status_code=403,
                    detail="Invalid invite key.",
                )

            # 3. Check for preexisting local accounts to avoid unnecessary cloud provisioning overhead
            existing_user = await self.user_repository.get_by_email(
                db=db,
                email=normalize_email(data.email),
            )

            if existing_user:
                raise HTTPException(
                    status_code=409,
                    detail="User already exists.",
                )

            #TODO: CHANGE THE SUPABASE AUTH PAYLOAD WITH CLASS MODEL
            # 4. Provision the primary credentials profile within Supabase Auth engine
            auth_response = supabase.auth.admin.create_user(
                {
                    "email": normalize_email(data.email),
                    "password": data.password,
                    "email_confirm": True, # Automatically verify email for instant workspace entry
                }
            )

            auth_user = auth_response.user
            
            if not auth_user:
                raise HTTPException(
                    status_code=500,
                    detail="Failed to create auth user.",
                )
            
            supabase_user_id = auth_user.id

            # 5. Formulate and create the local tracking application profile record
            user = {
                "supabase_uid": str(auth_user.id),
                "email": normalize_email(data.email),
                "full_name": data.full_name.strip(),
                "org_id": organization.id,
                "org_role": OrgRole.MEMBER.value,
            }
            
            user = await self.user_repository.create(
                db=db,
                data=user,
            )

            # Atomically commit both local profile creations and trigger flushes
            await db.commit()
            await db.refresh(instance=user)
            return user

        except IntegrityError:
            # Catch unexpected race-condition indexing violations at the database layer
            await db.rollback()
            self._cleanup_supabase_user(supabase_user_id)
            raise HTTPException(
                status_code=409,
                detail="User or organization data already exists.",
            )
        
        except Exception:
            # Catch broad application failures, roll back state, and clean up remote orphans
            await db.rollback()
            self._cleanup_supabase_user(supabase_user_id)
            raise


    async def login(
        self, 
        db: AsyncSession, 
        data: MemberLoginRequest, 
        ip_address: str | None
    ) -> TokenResponse:
        """
        Authenticates a member against Supabase Auth and generates a local access token.

        Verifies matching plaintext credentials, runs state checks on the user profile, 
        logs current security auditing metrics, and issues an signed internal system token.

        Args:
            db (AsyncSession): The active database communication transaction session.
            data (MemberLoginRequest): Input payload housing identity credentials.
            ip_address (str | None): Parsed client IP extracted from incoming connection context headers.

        Returns:
            TokenResponse: Serialization payload containing the token structure.

        Raises:
            HTTPException (401): If credential evaluation fails inside the identity provider.
            HTTPException (404): If a profile mapping matching the email cannot be resolved locally.
            HTTPException (403): If administrative locks are applied to the targeted profile.
        """
        # Authenticate credentials securely against Supabase Auth
        response = supabase.auth.sign_in_with_password(credentials={
            "email": normalize_email(data.email),
            "password": data.password
        })

        if not response.user:
            raise HTTPException(
                status_code=401,
                detail="Invalid Credentials."
            )
        
        # Resolve the local profile metadata tracking record
        user = await self.user_repository.get_by_email(
            db=db, 
            email=normalize_email(data.email)
        )

        if not user:
            raise HTTPException(
                status_code=404,
                detail="User not found."
            )
        
        # Enforce administrative security boundary checks
        if not user.is_active:
            raise HTTPException(
                status_code=403,
                detail="Inactive user."
            )
        
        try:
            # Update connection audit markers for security logging vectors
            user.last_login_at = datetime.now(UTC)
            user.last_login_ip = ip_address

            await db.commit()
        except Exception:
            await db.rollback()
            raise

        # Generate internal multi-tenant JWT claims payload
        access_token = create_access_token(
            data={
                "sub": str(user.id),
                "org_id": str(user.org_id),
                "org_role": user.org_role.value if isinstance(user.org_role, OrgRole) else user.org_role,
            }
        )

        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        )


    async def get_current_user_profile(
        self,
        db: AsyncSession,
        auth_context: AuthContext,
    ) -> User:
        """
        Resolves and verifies an active user profile using validated token metadata claims.

        Args:
            db (AsyncSession): The active database session context.
            auth_context (AuthContext): Validated session metadata token extracted by route guards.

        Returns:
            User: The verified, fully hydrated database profile record entity.

        Raises:
            HTTPException (401): If identity resolution maps fail or metadata claims conflict.
            HTTPException (403): If systemic blockages apply to the target identity.
        """
        user = await self.user_repository.get_by_id(
            db=db,
            entity_id=auth_context.user_id,
        )

        if not user:
            raise HTTPException(
                status_code=401,
                detail="User not found."
            )

        if not user.is_active:
            raise HTTPException(
                status_code=403,
                detail="Inactive user."
            )

        # Normalize the structural role format for evaluation comparison blocks
        user_role = user.org_role.value if isinstance(user.org_role, OrgRole) else user.org_role

        # Enforce multi-tenant access controls by verifying that the database context matches token claims
        if str(user.org_id) != str(auth_context.org_id) or user_role != auth_context.org_role.value:
            raise HTTPException(
                status_code=401,
                detail="Token claims do not match user."
            )
        
        return user

    
    def _cleanup_supabase_user(self, supabase_user_id: str | None) -> None:
        """Helper function to delete orphaned Supabase accounts if a database transaction fails."""
        
        if supabase_user_id:
            try:
                supabase.auth.admin.delete_user(supabase_user_id)
            except Exception:
                # Suppress errors inside cleanup block to preserve original bubbling exception trails
                pass