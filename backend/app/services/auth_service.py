from datetime import UTC, datetime

from fastapi import HTTPException

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from app.config import settings

from app.core.enums import OrgRole
from app.core.security import create_access_token

from app.core.security import decrypt_invite_key
from app.integrations.supabase_client import supabase

from app.models.user import User

from app.repositories.organization_repository import OrganizationRepository
from app.repositories.user_repository import UserRepository

from app.schemas import TokenResponse, MemberRegisterRequest, MemberLoginRequest
from app.schemas.auth import AuthContext

from app.utils.validators import normalize_email



class AuthService:
    def __init__(self):
        self.organization_repository = OrganizationRepository()
        self.user_repository = UserRepository()

    
    async def register_member(
        self,
        db: AsyncSession,
        data: MemberRegisterRequest,
    ) -> User:

        supabase_user_id = None

        try:
            organization = await self.organization_repository.get_by_slug(
                db,
                data.org_slug,
            )

            if not organization:
                raise HTTPException(
                    status_code=404,
                    detail="Organization not found.",
                )

            actual_invite_key = decrypt_invite_key(
                organization.encrypted_invite_key
            )

            if actual_invite_key != data.invite_key:
                raise HTTPException(
                    status_code=403,
                    detail="Invalid invite key.",
                )

            existing_user = await self.user_repository.get_by_email(
                db=db,
                email=normalize_email(data.email),
            )

            if existing_user:
                raise HTTPException(
                    status_code=409,
                    detail="User already exists.",
                )

            auth_response = supabase.auth.admin.create_user(
                {
                    "email": normalize_email(data.email),
                    "password": data.password,
                    "email_confirm": True,
                }
            )

            auth_user = auth_response.user
            
            if not auth_user:
                raise HTTPException(
                    status_code=500,
                    detail="Failed to create auth user.",
                )
            
            supabase_user_id = auth_user.id

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

            await db.commit()

            await db.refresh(user)

            return user

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
                detail="User or organization data already exists.",
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


    async def login(self, db: AsyncSession, data: MemberLoginRequest, ip_address: str | None) -> TokenResponse:
        response = supabase.auth.sign_in_with_password({
            "email": normalize_email(data.email),
            "password": data.password
        })

        if not response.user:
            raise HTTPException(
                status_code=401,
                detail="Invalid Credentials."
            )
        
        user = await self.user_repository.get_by_email(db=db, email=normalize_email(data.email))

        if not user:
            raise HTTPException(
                status_code=404,
                detail="User not found."
            )
        
        if not user.is_active:
            raise HTTPException(
                status_code=403,
                detail="Inactive user."
            )
        
        try:
            user.last_login_at = datetime.now(UTC)
            user.last_login_ip = ip_address

            await db.commit()
        except Exception:
            await db.rollback()
            raise

        access_token = create_access_token(
            data={
                "sub": str(user.id),
                "org_id": str(user.org_id),
                "org_role": user.org_role,
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

        if str(user.org_id) != str(auth_context.org_id) or user_role != auth_context.org_role.value:
            raise HTTPException(
                status_code=401,
                detail="Token claims do not match user."
            )
        
        return user
