from supabase import (
    Client, 
    create_client
)

from app.config import settings

# Initialize the Supabase Admin Client.
# This client uses the SERVICE_KEY, granting it administrative privileges
# that bypass Row Level Security (RLS). It should only be used in secure,
# server-side environments.
supabase: Client = create_client(
    supabase_url=settings.SUPABASE_URL,
    supabase_key=settings.SUPABASE_SERVICE_KEY
)