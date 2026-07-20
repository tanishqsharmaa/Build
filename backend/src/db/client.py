from supabase import create_client, Client
from src.core.config import settings

_client: Client | None = None


def get_supabase() -> Client:
    """Return a Supabase client authenticated with the service role key.

    The service role key bypasses RLS — only use server-side. Never expose to
    the frontend.
    """
    global _client
    if _client is None:
        _client = create_client(settings.supabase_url, settings.supabase_service_key)
    return _client
