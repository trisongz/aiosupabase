import re
from urllib.parse import urljoin
from typing import Optional, Dict, Union, Any

from lazyops.types import validator, BaseSettings, lazyproperty
from aiosupabase.version import VERSION
from postgrest.constants import DEFAULT_POSTGREST_CLIENT_TIMEOUT
from gotrue.constants import COOKIE_OPTIONS

from aiosupabase.types.errors import SupabaseException

class SupabaseSettings(BaseSettings):

    url: Optional[str] = None
    key: Optional[str] = None
    debug_enabled: Optional[bool] = False

    # Client Options
    client_schema: Optional[str] = "public"
    headers: Optional[Dict] = {}
    auto_refresh_token: Optional[bool] = True
    persist_session: Optional[bool] = True

    realtime_config: Optional[Dict[str, Any]] = None
    timeout: Optional[Union[int, float]] = DEFAULT_POSTGREST_CLIENT_TIMEOUT
    
    # Auth Client
    cookie_options: Optional[Dict] = COOKIE_OPTIONS
    replace_default_headers: Optional[bool] = False

    class Config:
        env_prefix = "SUPABASE_"
        case_sensitive = False
    
    @validator("url", pre = True, always = True)
    def validate_url(cls, value: str) -> str:
        if value is None: return value
        if not re.match(r"^(https?)://.+", value):
            raise SupabaseException(f"Invalid URL: {value}")
        return value

    @validator("key", pre = True, always = True)
    def validate_key(cls, value: str) -> str:
        if value is None: return value
        if not re.match(
            r"^[A-Za-z0-9-_=]+\.[A-Za-z0-9-_=]+\.?[A-Za-z0-9-_.+/=]*$", value
        ):
            raise SupabaseException(f"Invalid key: {value}")
        return value
    
    @lazyproperty
    def rest_url(self):
        return urljoin(self.url, "/rest/v1")
    
    @lazyproperty
    def realtime_url(self):
        return urljoin(self.url, "/realtime/v1").replace("http", "ws")
    
    @lazyproperty
    def auth_url(self):
        return urljoin(self.url, "/auth/v1")
    
    @lazyproperty
    def storage_url(self):
        return urljoin(self.url, "/storage/v1")

    @lazyproperty
    def is_platform(self):
        return re.search(r"(supabase\.co)|(supabase\.in)", self.url)
    
    @lazyproperty
    def functions_url(self):
        if self.is_platform:
            url_parts = self.url.split(".")
            return (
                f"{url_parts[0]}.functions.{url_parts[1]}.{url_parts[2]}"
            )
        return urljoin(self.url, "/functions/v1")


    @property
    def default_headers(self):
        return {
            "X-Client-Info": f"aiosupabase/{VERSION}",
            "Accept": "application/json",
            "Content-Type": "application/json",
            **self.headers,
        }


    def configure(
        self,
        *,
        url: Optional[str] = None,
        key: Optional[str] = None,
        debug_enabled: Optional[bool] = None,
        client_schema: Optional[str] = None,
        headers: Optional[Dict] = None,
        auto_refresh_token: Optional[bool] = None,
        persist_session: Optional[bool] = None,

        realtime_config: Optional[Dict[str, Any]] = None,
        timeout: Optional[Union[int, float]] = None,

        cookie_options: Optional[Dict] = None,
        replace_default_headers: Optional[bool] = None,
        **kwargs,
    ):
        """
        Configure the global supabase settings

        :param url: the supabase url
        :param key: the supabase key
        :param debug_enabled: whether to enable debug mode
        :param client_schema: the supabase client schema
        :param headers: the headers to send with requests
        :param auto_refresh_token: whether to automatically refresh the token
        :param persist_session: whether to persist the session
        :param realtime_config: the supabase realtime config
        :param timeout: the timeout in seconds
        :param cookie_options: the cookie options
        :param replace_default_headers: whether to replace the default headers
        """

        if url is not None: self.url = url
        if key is not None: self.key = key
        if debug_enabled is not None: self.debug_enabled = debug_enabled
        if client_schema is not None: self.client_schema = client_schema
        if headers is not None: self.headers = headers
        if auto_refresh_token is not None: self.auto_refresh_token = auto_refresh_token
        if persist_session is not None: self.persist_session = persist_session
        if realtime_config is not None: self.realtime_config = realtime_config
        if timeout is not None: self.timeout = timeout
        if cookie_options is not None: self.cookie_options = cookie_options
        if replace_default_headers is not None: self.replace_default_headers = replace_default_headers
        for k,v in kwargs.items():
            if v is None: continue
            if hasattr(self, k):
                setattr(self, k, v)


settings = SupabaseSettings()
