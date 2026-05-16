from fastapi import HTTPException

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from app.core.security import (
    generate_invite_key, 
    create_access_token, 
    encrypt_invite_key, 
    decrypt_invite_key
)
from app.core.enums import OrgRole
from app.config import settings
from app.integrations.supabase_client import supabase
from app.models import Organization
from app.repositories import (
    OrganizationRepository, 
    UserRepository
)
from app.schemas import (
    SetupOrganizationRequest, 
    SetupOrganizationResponse, 
    OrganizationResponse, 
    AuthContext
)
from app.utils.validators import normalize_email

class OrganizationService:
    """
    Business service layer orchestrating Organization Provisioning and Tenant Configurations.

    Manages multi-tenant space setup, slug uniqueness routing verification, and restricted 
    cryptographic workspace invitation key exposures.
    """

    def __init__(self):
        """Initializes the service and encapsulates data access repository dependencies."""
        self.organization_repository = OrganizationRepository()
        self.user_repository = UserRepository()


    async def check_slug_availability(self, db: AsyncSession, slug: str) -> bool:
        """
        Verifies if a requested organization URL slug path is available for registration.

        Args:
            db (AsyncSession): The active database communication transaction frame.
            slug (str): The pre-sanitized string path to evaluate against the database index.

        Returns:
            bool: True if the path is entirely free for use; False if a conflict exists.
        """
        existing_org = await self.organization_repository.get_by_slug(
            db=db,
            slug=slug
        )

        return existing_org is None
    

    async def setup_organization(
        self, 
        db: AsyncSession, 
        data: SetupOrganizationRequest, 
        ip_address: str | None = None
    ) -> SetupOrganizationResponse:

        """
        Executes an atomic platform bootstrapping sequence for a new tenant workspace.

        Validates uniqueness constraints, creates an organization record, generates and encrypts 
        a workspace invitation key, provisions an identity profile in Supabase Auth, links the 
        local User record as the workspace OWNER, and issues an immediate session access token.

        Args:
            db (AsyncSession): The active asynchronous database unit-of-work transaction block.
            data (SetupOrganizationRequest): Validated workspace bootstrapping payload parameters.
            ip_address (str | None): Parsed caller source IP to append to audit log records.

        Returns:
            SetupOrganizationResponse: Compound payload with token parameters and workspace profiles.

        Raises:
            HTTPException (409): If the requested routing slug or owner email is pre-registered.
            HTTPException (500): If unexpected synchronization failures occur with Supabase Auth.
        """

        supabase_user_id = None

        try:
            # 1. Pre-flight Check: Enforce uniqueness boundaries on the routing slug path
            existing_org = await self.organization_repository.get_by_slug(
                db=db,
                slug=data.slug
            )

            if existing_org:
                raise HTTPException(
                    status_code=409,
                    detail="Slug already exists."
                )
            
            # 2. Pre-flight Check: Enforce uniqueness boundaries on the workspace owner identity
            existing_user = await self.user_repository.get_by_email(
                db=db,
                email=normalize_email(data.owner_email)
            )

            if existing_user:
                raise HTTPException(
                    status_code=409,
                    detail="User already exists."
                )
            
            # 3. Generate the workspace invitation token pair
            raw_invite_key = generate_invite_key()

            organization_data = {
                "name": data.organization_name.strip(),
                "slug": data.slug,
                "encrypted_invite_key": encrypt_invite_key(raw_invite_key)
            }
            
            # Persist organization records into the open database frame
            organization = await self.organization_repository.create(
                db=db,
                data=organization_data
            )

            # 4. Provision primary administrative credentials within Supabase Auth engine
            auth_response = supabase.auth.admin.create_user({
                "email": normalize_email(email=data.owner_email),
                "password": data.password,
                "email_confirm": True # Auto-confirm owner profiles for instant redirection loops
            })

            auth_user = auth_response.user

            if not auth_user:
                raise HTTPException(
                    status_code=500,
                    detail="Failed to create auth user."
                )
            
            supabase_user_id = auth_user.id

            # 5. Populate the internal tracking database profile record
            user_data = {
                "supabase_uid": str(auth_user.id),
                "email": normalize_email(email=data.owner_email),
                "full_name": data.owner_name.strip(),
                "org_id": organization.id,
                "org_role": OrgRole.OWNER.value,
                "last_login_ip": ip_address
            }

            user = await self.user_repository.create(
                db=db,
                data=user_data
            )

            # 6. Establish the circular relationship bridge by anchoring the owner ID back onto the organization
            organization.owner_id = user.id

            # Push changes downstream to validate constraints before triggering a hard commit
            await db.flush()
            await db.commit()
            await db.refresh(organization)

            # 7. Generate structural multi-tenant JWT claims access parameters
            access_token = create_access_token(
                data={
                    "sub": str(user.id),
                    "org_id": str(user.org_id),
                    "org_role": user.org_role
                }
            )

            return SetupOrganizationResponse(
                access_token=access_token,
                token_type="bearer",
                expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
                invite_key=raw_invite_key, # Exposed raw exactly once here
                organization=OrganizationResponse.model_validate(obj=organization)
            )

        except IntegrityError:
            # Trap racing transaction indexing conflicts at the database layer
            await db.rollback()
            self._cleanup_supabase_user(supabase_user_id)
            raise HTTPException(
                status_code=409,
                detail="Organization slug or owner email already exists.",
            )

        except Exception:
            # General safe recovery path: revert partial states and scrub orphaned identities
            await db.rollback()
            self._cleanup_supabase_user(supabase_user_id)
            raise

    
    async def get_invite_key(
        self,
        organization: Organization,
    ) -> str:
        """
        Decrypts an organization's workspace entry token into plaintext.

        Internal service helper. Assumes access privileges have been validated by callers.
        """
        return decrypt_invite_key(
            encrypted_invite_key=organization.encrypted_invite_key
        )


    async def get_invite_key_for_owner(
        self,
        db: AsyncSession,
        auth_context: AuthContext,
    ) -> str:
        """
        Validates caller credentials and exposes the unencrypted workspace invitation token.

        Enforces security checks: ensures user profile is active, matches the targeted 
        tenant workspace boundaries, and bears the explicit administrative OWNER rank.

        Args:
            db (AsyncSession): The active database transaction session.
            auth_context (AuthContext): Validated identity claims payload extracted from route guards.

        Returns:
            str: The raw, plaintext secret workspace entry string.

        Raises:
            HTTPException (401): If individual profile records cannot be resolved.
            HTTPException (403): If the profile fails access authorization checks.
            HTTPException (404): If organization data stores are missing.
        """
        # 1. Identity Verification Lookup
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

        # 2. Multi-Tenant Tenancy Validation Guard
        if str(user.org_id) != str(auth_context.org_id):
            raise HTTPException(
                status_code=403,
                detail="User does not belong to this organization."
            )

        # 3. Role-Based Privilege Evaluation
        user_role = user.org_role.value if isinstance(user.org_role, OrgRole) else user.org_role
        if user_role != OrgRole.OWNER.value:
            raise HTTPException(
                status_code=403,
                detail="Only organization owners can access invite keys."
            )

        # 4. Target Workspace Identity Resolution
        organization = await self.organization_repository.get_by_id(
            db=db,
            entity_id=auth_context.org_id,
        )
        if not organization:
            raise HTTPException(
                status_code=404,
                detail="Organization not found."
            )

        # 5. Cryptographic Ownership Verification Check
        if organization.owner_id != user.id:
            raise HTTPException(
                status_code=403,
                detail="Only the organization owner can access invite keys."
            )

        # Execute decryption pipeline if structural validation targets pass
        return await self.get_invite_key(
            organization=organization,
        )
    

    #TODO: IMPLEMENT ROTATE INVITE KEY


    def _cleanup_supabase_user(self, supabase_user_id: str | None) -> None:
        """Helper to clear orphaned credentials from Supabase if local transactions fail."""
        if supabase_user_id:
            try:
                supabase.auth.admin.delete_user(supabase_user_id)
            except Exception:
                pass