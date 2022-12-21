
from aiosupabase.schemas import *
from aiosupabase.utils.config import SupabaseSettings
from aiosupabase.utils.config import settings as sb_settings
from gotrue.types import (
    CookieOptions,
)
from postgrest import (
    SyncFilterRequestBuilder, 
    SyncRequestBuilder,
    AsyncRequestBuilder,
    AsyncFilterRequestBuilder,
    
)
from gotrue import (
    CookieOptions,
    SyncGoTrueAPI,
    SyncSupportedStorage,
    AsyncGoTrueAPI,
    AsyncSupportedStorage,
)
from realtime.connection import Socket
from typing import Dict, Optional, Union, Any

class SupabaseClient:
    
    def __init__(
        self,
        url: Optional[str] = None,
        key: Optional[str] = None,
        headers: Optional[Dict] = None,
        schema: Optional[str] = None,
        timeout: Optional[int] = None,
        auto_refresh_token: Optional[bool] = None,
        persist_session: Optional[bool] = None,
        cookie_options: Optional[Union[CookieOptions, Dict]] = None,
        replace_default_headers: Optional[bool] = None,

        local_storage: Optional[SyncSupportedStorage] = None,
        api: Optional[SyncGoTrueAPI] = None,

        async_local_storage: Optional[AsyncSupportedStorage] = None,
        async_api: Optional[AsyncGoTrueAPI] = None,
        settings: Optional[SupabaseSettings] = None,

    ):
        """
        The Supabase Client
        """
        self.settings = settings if settings is None else sb_settings
        self.url = url if url is not None else self.settings.url
        self.key = key if key is not None else self.settings.key
        self.default_headers = headers if headers is not None else self.settings.default_headers

        # These will be set from the settings per app
        self.auth: SupabaseAuthClient = SupabaseAuthClient(
            auto_refresh_token = auto_refresh_token,
            persist_session = persist_session,
            cookie_options = cookie_options,
            replace_default_headers = replace_default_headers,

            api = api,
            local_storage = local_storage,

            async_api = async_api,
            async_local_storage = async_local_storage,
            settings = self.settings,
        )
        self.socket = Socket(
            url = self.settings.realtime_url,
        )
        self._realtime_clients: Dict[str, SupabaseRealtimeClient] = {}
        self.postgrest: SupabasePostgrestClient = SupabasePostgrestClient(
            schema = schema,
            timeout = timeout,
            settings = self.settings,
        )
        self._storage: SupabaseStorageClient = SupabaseStorageClient(
            settings = self.settings,
        )
        self._functions: FunctionsClient = FunctionsClient(
            settings = self.settings,
        )
    
    def set_auth(
        self, 
        token: str,
        *,
        username: Union[str, bytes, None] = None,
        password: Union[str, bytes] = "",    
    ) -> None:
        """Updates the authorization header

        Parameters
        ----------
        token : str
            the new jwt token sent in the authorisation header
        """

        self.postgrest.auth(token = token, username = username, password = password)
        self.auth.set_auth(access_token = token)
        self._functions.set_auth(token = token)
    
    @property
    def functions(self) -> FunctionsClient:
        return self._functions
    
    @property
    def storage(self) -> SupabaseStorageClient:
        return self._storage
    
    def realtime(self, table_name: Optional[str] = "*", schema: Optional[str] = None) -> SupabaseRealtimeClient:
        """
        Returns a realtime client for the given table.

        Parameters
        ----------
        table_name : str, optional
        schema : str, optional

        Returns
        -------
        SupabaseRealtimeClient
        """
        if schema is None: schema = self.settings.client_schema
        if table_name not in self._realtime_clients:
            self._realtime_clients[table_name] = SupabaseRealtimeClient(
                socket = self.socket,
                schema = schema,
                table_name = table_name,
            )
        return self._realtime_clients[table_name]

    def from_(self, table_name: str) -> SyncRequestBuilder:
        """Perform a table operation.
        See the `table` method.
        """
        return self.postgrest.from_(table_name)
    

    def afrom_(self, table_name: str) -> AsyncRequestBuilder:
        """[Async] Perform a table operation.
        See the `atable` method.
        """
        return self.postgrest.afrom_(table_name)


    def table(self, table_name: str) -> SyncRequestBuilder:
        """Perform a table operation.
        Note that the supabase client uses the `from` method, but in Python,
        this is a reserved keyword, so we have elected to use the name `table`.
        Alternatively you can use the `.from_()` method.
        """
        return self.from_(table_name)

    def atable(self, table_name: str) -> AsyncRequestBuilder:
        """[Async] Perform a table operation.
        Note that the supabase client uses the `from` method, but in Python,
        this is a reserved keyword, so we have elected to use the name `table`.
        Alternatively you can use the `.from_()` method.
        """
        return self.afrom_(table_name)

    def rpc(self, fn: str, params: Dict[Any, Any]) -> SyncFilterRequestBuilder:
        """Performs a stored procedure call.
        Parameters
        ----------
        fn : callable
            The stored procedure call to be executed.
        params : dict of any
            Parameters passed into the stored procedure call.
        Returns
        -------
        SyncFilterRequestBuilder
            Returns a filter builder. This lets you apply filters on the response
            of an RPC.
        """
        return self.postgrest.rpc(fn, params)

    async def async_rpc(self, fn: str, params: Dict[Any, Any]) -> AsyncFilterRequestBuilder:
        """[Async] Performs a stored procedure call.
        Parameters
        ----------
        fn : callable
            The stored procedure call to be executed.
        params : dict of any
            Parameters passed into the stored procedure call.
        Returns
        -------
        SyncFilterRequestBuilder
            Returns a filter builder. This lets you apply filters on the response
            of an RPC.
        """
        return await self.postgrest.async_rpc(fn, params)



    """
    Context Managers
    """

    async def aclose(self):
        await self.postgrest.aclose()
        await self.auth.aclose()
        await self.storage.aclose()
        await self.functions.aclose()
    
    def close(self):
        self.postgrest.close()
        self.auth.close()
        self.storage.close()
        self.functions.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_value, traceback):
        self.close()
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_value, traceback):
        await self.aclose()



class SupabaseAPI:
    settings: Optional[SupabaseSettings] = sb_settings
    _api: Optional[SupabaseClient] = None

    """
    The Global Class for Supabase API.
    """

    def configure(
        self, 
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
        reset: Optional[bool] = None,
        **kwargs
    ):
        """
        Configure the global Supabase client.

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
        self.settings.configure(
            url=url,
            key=key,
            debug_enabled=debug_enabled,
            client_schema=client_schema,
            headers=headers,
            auto_refresh_token=auto_refresh_token,
            persist_session=persist_session,
            realtime_config=realtime_config,
            timeout=timeout,
            cookie_options=cookie_options,
            replace_default_headers=replace_default_headers,
            **kwargs
        )
        if reset: self._api = None
        if self._api is None:
            self.get_api(**kwargs)
    
    def get_api(self, **kwargs) -> SupabaseClient:
        if self._api is None:
            self._api = SupabaseClient(
                settings = self.settings,
                **kwargs
            )
        return self._api
    

    @property
    def api(self) -> SupabaseClient:
        """
        Returns the inherited Supabase client.
        """
        if self._api is None:
            self.configure()
        return self._api

    @property
    def auth(self) -> SupabaseAuthClient:
        return self.api.auth
    
    @property
    def postgrest(self) -> SupabasePostgrestClient:
        return self.api.postgrest
    
    @property
    def storage(self) -> SupabaseStorageClient:
        return self.api.storage
    
    @property
    def functions(self) -> FunctionsClient:
        return self.api.functions

    def realtime(self, table_name: Optional[str] = "*", schema: Optional[str] = None) -> SupabaseRealtimeClient:
        """
        Returns a realtime client for the given table.

        Parameters
        ----------
        table_name : str, optional
        schema : str, optional

        Returns
        -------
        SupabaseRealtimeClient
        """
        return self.api.realtime(table_name=table_name, schema=schema)

    """
    Subclassing
    """

    def set_auth(
        self, 
        token: str,
        *,
        username: Union[str, bytes, None] = None,
        password: Union[str, bytes] = "",    
    ) -> None:
        """Updates the authorization header

        Parameters
        ----------
        token : str
            the new jwt token sent in the authorisation header
        """
        return self.api.set_auth(token, username = username, password = password)

    
    @property
    def functions(self) -> FunctionsClient:
        return self.api.functions
    
    @property
    def storage(self) -> SupabaseStorageClient:
        return self.api.storage
    

    def from_(self, table_name: str) -> SyncRequestBuilder:
        """Perform a table operation.
        See the `table` method.
        """
        return self.api.from_(table_name)
    

    def afrom_(self, table_name: str) -> AsyncRequestBuilder:
        """[Async] Perform a table operation.
        See the `atable` method.
        """
        return self.api.afrom_(table_name)


    def table(self, table_name: str) -> SyncRequestBuilder:
        """Perform a table operation.
        Note that the supabase client uses the `from` method, but in Python,
        this is a reserved keyword, so we have elected to use the name `table`.
        Alternatively you can use the `.from_()` method.
        """
        return self.api.table(table_name)

    def atable(self, table_name: str) -> AsyncRequestBuilder:
        """[Async] Perform a table operation.
        Note that the supabase client uses the `from` method, but in Python,
        this is a reserved keyword, so we have elected to use the name `table`.
        Alternatively you can use the `.from_()` method.
        """
        return self.api.atable(table_name)

    def rpc(self, fn: str, params: Dict[Any, Any]) -> SyncFilterRequestBuilder:
        """Performs a stored procedure call.
        Parameters
        ----------
        fn : callable
            The stored procedure call to be executed.
        params : dict of any
            Parameters passed into the stored procedure call.
        Returns
        -------
        SyncFilterRequestBuilder
            Returns a filter builder. This lets you apply filters on the response
            of an RPC.
        """
        return self.api.rpc(fn, params)

    async def async_rpc(self, fn: str, params: Dict[Any, Any]) -> AsyncFilterRequestBuilder:
        """[Async] Performs a stored procedure call.
        Parameters
        ----------
        fn : callable
            The stored procedure call to be executed.
        params : dict of any
            Parameters passed into the stored procedure call.
        Returns
        -------
        SyncFilterRequestBuilder
            Returns a filter builder. This lets you apply filters on the response
            of an RPC.
        """
        return await self.api.async_rpc(fn, params)


    """
    Context Managers
    """

    async def aclose(self):
        if self._api is not None:
            await self._api.aclose()
    
    def close(self):
        if self._api is not None:
            self._api.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_value, traceback):
        self.close()
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_value, traceback):
        await self.aclose()

Supabase: SupabaseAPI = SupabaseAPI()
