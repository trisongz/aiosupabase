import aiohttpx

from typing import Dict, Optional, Union, Any, Callable
from postgrest import (
    SyncFilterRequestBuilder, 
    SyncRequestBuilder,
    AsyncRequestBuilder,
    AsyncFilterRequestBuilder,
    
)
from aiosupabase.utils.config import SupabaseSettings
from aiosupabase.utils.config import settings as sb_settings
from lazyops.types import lazyproperty


class SupabasePostgrestClient:

    """
    SupabasePostgrestClient that wraps both
    async and sync
    """

    def __init__(
        self,
        url: Optional[str] = None,
        key: Optional[str] = None,
        headers: Optional[Dict] = None,
        schema: Optional[str] = None,
        timeout: Optional[int] = None,
        settings: Optional[SupabaseSettings] = None,
    ):

        self.settings = settings if settings is None else sb_settings
        self.url = url if url is not None else self.settings.rest_url
        self.key = key if key is not None else self.settings.key
        self.default_headers = headers if headers is not None else self.settings.default_headers
        self.timeout = timeout if timeout is not None else self.settings.timeout
        self._schema = schema if schema is not None else self.settings.client_schema

        self._session: aiohttpx.Client = None
        

    """
    Methods
    """
    def from_(self, table: str) -> SyncRequestBuilder:
        """Perform a table operation.

        Args:
            table: The name of the table
        Returns:
            :class:`SyncRequestBuilder`
        """
        return SyncRequestBuilder(self.session.sync_client, f"/{table}")
    
    def afrom_(self, table: str) -> AsyncRequestBuilder:
        """[Async] Perform a table operation.

        Args:
            table: The name of the table
        Returns:
            :class:`AsyncRequestBuilder`
        """
        return AsyncRequestBuilder(self.session.async_client, f"/{table}")
    
    def table(self, table: str) -> SyncRequestBuilder:
        """Alias to :meth:`from_`."""
        return self.from_(table)
    
    def atable(self, table: str) -> AsyncRequestBuilder:
        """[Async] Alias to :meth:`from_`."""
        return self.afrom_(table)
    
    def from_table(self, table: str) -> SyncRequestBuilder:
        """Alias to :meth:`from_`."""
        return self.from_(table)
    
    def async_from_table(self, table: str) -> AsyncRequestBuilder:
        """[Async] Alias to :meth:`from_`."""
        return self.afrom_(table)

    def rpc(self, func: str, params: dict) -> SyncFilterRequestBuilder:
        """Perform a stored procedure call.

        Args:
            func: The name of the remote procedure to run.
            params: The parameters to be passed to the remote procedure.
        Returns:
            :class:`AsyncFilterRequestBuilder`
        Example:
            .. code-block:: python

                await client.rpc("foobar", {"arg": "value"}).execute()

        .. versionchanged:: 0.11.0
            This method now returns a :class:`AsyncFilterRequestBuilder` which allows you to
            filter on the RPC's resultset.
        """
        # the params here are params to be sent to the RPC and not the queryparams!
        return SyncFilterRequestBuilder(
            self.session.sync_client,
            f"/rpc/{func}", 
            "POST", 
            aiohttpx.Headers(), 
            aiohttpx.QueryParams(), 
            json = params
        )

    async def async_rpc(self, func: str, params: dict) -> AsyncFilterRequestBuilder:
        """Perform a stored procedure call.

        Args:
            func: The name of the remote procedure to run.
            params: The parameters to be passed to the remote procedure.
        Returns:
            :class:`AsyncFilterRequestBuilder`
        Example:
            .. code-block:: python

                await client.rpc("foobar", {"arg": "value"}).execute()

        .. versionchanged:: 0.11.0
            This method now returns a :class:`AsyncFilterRequestBuilder` which allows you to
            filter on the RPC's resultset.
        """
        # the params here are params to be sent to the RPC and not the queryparams!
        return AsyncFilterRequestBuilder(
            self.session.async_client, 
            f"/rpc/{func}", 
            "POST", 
            aiohttpx.Headers(), 
            aiohttpx.QueryParams(), 
            json = params
        )

    @lazyproperty
    def headers(self):
        _headers = self.default_headers.copy()
        if self.settings.key:
            _headers["apiKey"] = self.settings.key
            _headers["Authorization"] = f"Bearer {self.settings.key}"
        _headers["Accept-Profile"] = self._schema
        _headers["Content-Profile"] = self._schema
        return _headers

    @property
    def session(self) -> aiohttpx.Client:
        if self._session is None: self._session = self.create_session()
        return self._session

    def create_session(
        self,
        base_url: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None,
        timeout: Optional[Union[int, float, aiohttpx.Timeout]] = None,
    ) -> aiohttpx.Client:
        base_url = base_url if base_url is not None else self.url
        headers = headers if headers is not None else self.headers
        timeout = timeout if timeout is not None else self.timeout
        return aiohttpx.Client(
            base_url=base_url,
            headers=headers,
            timeout=timeout,
        )

    def auth(
        self,
        token: Optional[str],
        *,
        username: Union[str, bytes, None] = None,
        password: Union[str, bytes] = "",
    ):
        """
        Authenticate the client with either bearer token or basic authentication.

        Raises:
            `ValueError`: If neither authentication scheme is provided.

        .. note::
            Bearer token is preferred if both ones are provided.
        """
        if token:
            if self._session:
                self.session.headers["Authorization"] = f"Bearer {token}"
            else:
                self.default_headers["Authorization"] = f"Bearer {token}"
        elif username:
            if self._session:
                self.session.auth = aiohttpx.BasicAuth(username, password)
            else:
                self.default_headers["Authorization"] = aiohttpx.BasicAuth(username, password)._auth_header
        else:
            raise ValueError(
                "Neither bearer token or basic authentication scheme is provided"
            )
        return self
    
    def schema(self, schema: str):
        """Switch to another schema."""
        self.session.headers.update(
            {
                "Accept-Profile": schema,
                "Content-Profile": schema,
            }
        )
        return self

    
    async def __aenter__(self) -> 'SupabasePostgrestClient':
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        await self.aclose()

    async def aclose(self) -> None:
        """Close the underlying HTTP connections."""
        if self._session is not None:
            await self._session.aclose()
            self._session = None
    
    def __enter__(self) -> 'SupabasePostgrestClient':
        return self
    
    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()

    def close(self) -> None:
        """Close the underlying HTTP connections."""
        if self._session is not None:
            self._session.close()
            self._session = None
    