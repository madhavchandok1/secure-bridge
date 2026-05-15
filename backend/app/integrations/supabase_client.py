from supabase import Client, create_client

from app.config import settings


supabase: Client = create_client(
    supabase_url=settings.SUPABASE_URL,
    supabase_key=settings.SUPABASE_SERVICE_KEY
)