from __future__ import absolute_import

from aiosupabase.utils.config import SupabaseSettings, settings
from aiosupabase.types.errors import (
    SupabaseException,
)

from aiosupabase.schemas.auth import SupabaseAuthClient
from aiosupabase.schemas.pgrest import SupabasePostgrestClient
from aiosupabase.schemas.rt import SupabaseRealtimeClient
from aiosupabase.schemas.storage import SupabaseStorageClient
from aiosupabase.schemas.funcs import FunctionsClient

from aiosupabase.client import SupabaseClient, SupabaseAPI, Supabase
