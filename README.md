# aiosupabase
 Unofficial Asyncronous Python Client for Supabase

 **Latest Version**: [![PyPI version](https://badge.fury.io/py/aiosupabase.svg)](https://badge.fury.io/py/aiosupabase)



## Features

- Unified Asyncronous and Syncronous Python Client for [Supabase](https://supabase.com/)
- Supports Python 3.6+
- Strongly Typed with [Pydantic](https://pydantic-docs.helpmanual.io/)
- Utilizes Environment Variables for Configuration

## APIs

Both async and sync Apis are available for the following

- [x] Auth
- [x] Postgrest
- [x] Storage
- [x] Realtime
- [x] Functions

---

## Installation

```bash
# Install from PyPI
pip install aiosupabase

# Install from source
pip install git+https://github.com/trisongz/aiosupabase.git
```

## Usage

Example Usage

```python
import asyncio
from aiosupabase import Supabase
from aiosupabase.utils import logger

"""
Environment Vars that map to Supabase.configure:
all vars are prefixed with SUPABASE_

SUPABASE_URL (url): str   | Supabase URL
SUPABASE_KEY (key): str   | API Key
SUPABASE_DEBUG_ENABLED (debug_enabled): bool - defaults to False

SUPABASE_CLIENT_SCHEMA (client_schema): str - defaults to 'public'
SUPABASE_HEADERS (headers): Dict - defaults to {}
SUPABASE_AUTO_REFRESH_TOKENS (auto_refresh_tokens): bool - defaults to True
SUPABASE_PERSIST_SESSION (persist_session): bool - defaults to True
SUPABASE_REALTIME_CONFIG (realtime_config): Dict - defaults to None
SUPABASE_TIMEOUT (timeout): int - defaults to 5 [DEFAULT_POSTGREST_CLIENT_TIMEOUT]

SUPABASE_COOKIE_OPTIONS (cookie_options): Dict - defaults to None
SUPABASE_REPLACE_DEFAULT_HEADERS (replace_default_headers): bool - defaults to False

"""

Supabase.configure(
    url = '...',
    key = "...",
    debug_enabled = True,
)

async def async_fetch_table(table: str = "profiles", select: str = "*"):
    # Async fetch
    # note that table is `atable` for async
    return await Supabase.atable(table).select(select).execute()

def fetch_table(table: str = "profiles", select: str = "*"):
    # Sync fetch
    return Supabase.table(table).select(select).execute()

async def async_fetch_users():
    # Async `ListUsers`
    # note that most async methods are prefixed with
    # `async_` 
    return await Supabase.auth.async_list_users()

def fetch_users():
    # Sync `ListUsers`
    # note that most async methods are prefixed with
    return Supabase.auth.list_users()

async def run_test():
    # Async fetch
    async_data = await async_fetch_table()
    logger.info(f"async_data: {async_data}")

    async_users = await async_fetch_users()
    logger.info(f"async_users: {async_users}")

    # Sync fetch
    sync_data = fetch_table()
    logger.info(f"sync_data: {sync_data}")

    sync_users = fetch_users()
    logger.info(f"sync_users: {sync_users}")


asyncio.run(run_test())

```