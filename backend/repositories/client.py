from __future__ import annotations

from functools import lru_cache
from supabase import Client, create_client
import config


@lru_cache(maxsize=1)
def _get_client() -> Client:
    if not config.SUPABASE_URL or not config.SUPABASE_KEY:
        raise ValueError(
            "SUPABASE_URL and SUPABASE_KEY must be set in your .env file."
        )
    return create_client(config.SUPABASE_URL, config.SUPABASE_KEY)
