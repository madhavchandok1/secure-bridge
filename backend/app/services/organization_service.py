from fastapi import HTTPException

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from app.core.security import generate_invite_key, create_access_token, encrypt_invite_key, decrypt_invite_key
from app.core.enums import OrgRole

from app.config import settings

from app.models import Organization

from app.repositories import OrganizationRepository, UserRepository

from app.schemas import SetupOrganizationRequest, SetupOrganizationResponse, OrganizationResponse
from app.schemas.auth import AuthContext

from app.utils.validators import normalize_email

from app.integrations.supabase_client import supabase

class OrganizationService:
    def __init__(self):
        self.organization_repository = OrganizationRepository()
        self.user_repository = UserRepository()


    async def check_slug_availability(self, db: AsyncSession, slug: str) -> bool:
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

        supabase_user_id = None

        try:
            existing_org = await self.organization_repository.get_by_slug(
                db=db,
                slug=data.slug
            )

            if existing_org:
                raise HTTPException(
                    status_code=409,
                    detail="Slug already exists."
                )
            
            existing_user = await self.user_repository.get_by_email(
                db=db,
                email=normalize_email(data.owner_email)
            )

            if existing_user:
                raise HTTPException(
                    status_code=409,
                    detail="User already exists."
                )
            
            raw_invite_key = generate_invite_key()

            organization_data = {
                "name": data.organization_name.strip(),
                "slug": data.slug,
                "encrypted_invite_key": encrypt_invite_key(raw_invite_key)
            }
            
            organization = await self.organization_repository.create(
                db=db,
                data=organization_data
            )

            auth_response = supabase.auth.admin.create_user({
                "email": normalize_email(email=data.owner_email),
                "password": data.password,
                "email_confirm": True
            })

            auth_user = auth_response.user

            if not auth_user:
                raise HTTPException(
                    status_code=500,
                    detail="Failed to create auth user."
                )
            
            supabase_user_id = auth_user.id

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

            organization.owner_id = user.id
            await db.flush()
            await db.commit()
            await db.refresh(organization)

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
                invite_key=raw_invite_key,
                organization=OrganizationResponse.model_validate(obj=organization)
            )

        except IntegrityError:
            await db.rollback()

            if supabase_user_id:
                try:
                    supabase.auth.admin.delete_user(
                        supabase_user_id
                    )
                except Exception:
                    pass

            raise HTTPException(
                status_code=409,
                detail="Organization slug or owner email already exists.",
            )


        except Exception:
            await db.rollback()

            if supabase_user_id:
                try:
                    supabase.auth.admin.delete_user(
                        supabase_user_id
                    )
                except Exception:
                    pass

            raise

    
    async def get_invite_key(
        self,
        organization: Organization,
    ) -> str:
        return decrypt_invite_key(
            organization.encrypted_invite_key
        )


    async def get_invite_key_for_owner(
        self,
        db: AsyncSession,
        auth_context: AuthContext,
    ) -> str:
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

        user_role = user.org_role.value if isinstance(user.org_role, OrgRole) else user.org_role

        if str(user.org_id) != str(auth_context.org_id):
            raise HTTPException(
                status_code=403,
                detail="User does not belong to this organization."
            )

        if user_role != OrgRole.OWNER.value:
            raise HTTPException(
                status_code=403,
                detail="Only organization owners can access invite keys."
            )

        organization = await self.organization_repository.get_by_id(
            db=db,
            entity_id=auth_context.org_id,
        )

        if not organization:
            raise HTTPException(
                status_code=404,
                detail="Organization not found."
            )

        if organization.owner_id != user.id:
            raise HTTPException(
                status_code=403,
                detail="Only the organization owner can access invite keys."
            )

        return await self.get_invite_key(
            organization=organization,
        )
    

    #TODO: IMPLEMENT ROTATE INVITE KEY
