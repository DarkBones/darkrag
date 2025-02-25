"""
Supabase wrapper module.
"""

import os
from typing import Optional

from supabase import Client, create_client


class Supabase:
    """
    A singleton wrapper for the Supabase client.
    """

    _instance: Optional["Supabase"] = None
    _client: Optional[Client] = None

    def __new__(cls) -> "Supabase":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.__init__()
        return cls._instance

    def __init__(self) -> None:
        """
        Initialize the Supabase client with environment variables.
        """

        if self._client is not None:
            return

        url = os.environ.get("SUPABASE_URL")
        key = os.environ.get("SUPABASE_KEY")

        if not url or not key:
            raise ValueError(
                "SUPABASE_URL and SUPABASE_KEY environment variables must be set"
            )

        self._client = create_client(url, key)

    def __getattr__(self, name: str):
        return getattr(self._client, name)
