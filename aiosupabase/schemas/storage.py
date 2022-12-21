import aiohttpx
from typing import Dict, Optional
from storage3._async.file_api import AsyncBucketProxy
from storage3._sync.file_api import SyncBucketProxy

from aiosupabase.utils.config import SupabaseSettings
from aiosupabase.utils.config import settings as sb_settings
from lazyops.types import lazyproperty

class SupabaseStorageClient:
    """
    Manage storage buckets and files
    that wraps both
    async and sync
    """

    def __init__(
        self,
        url: Optional[str] = None,
        key: Optional[str] = None,
        headers: Optional[Dict] = None,
        settings: Optional[SupabaseSettings] = None,
    ):

        self.settings = settings if settings is None else sb_settings
        self.url = url if url is not None else self.settings.storage_url
        self.key = key if key is not None else self.settings.key
        self.default_headers = headers if headers is not None else self.settings.default_headers
        self._session: aiohttpx.Client = None


    @property
    def session(self) -> aiohttpx.Client:
        if self._session is None: self._session = self.create_session()
        return self._session

    def create_session(
        self,
        base_url: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> aiohttpx.Client:
        base_url = base_url if base_url is not None else self.url
        headers = headers if headers is not None else self.headers
        return aiohttpx.Client(
            base_url=base_url,
            headers=headers,
        )

    @lazyproperty
    def headers(self):
        _headers = self.default_headers.copy()
        if self.settings.key:
            _headers["apiKey"] = self.settings.key
            _headers["Authorization"] = f"Bearer {self.settings.key}"
        return _headers

    """
    Functions
    """

    def from_(self, id: str) -> SyncBucketProxy:
        """[Sync] Run a storage file operation.

        Parameters
        ----------
        id
            The unique identifier of the bucket
        """
        return SyncBucketProxy(id, self.session.sync_client)
    

    def afrom_(self, id: str) -> AsyncBucketProxy:
        """[Async] Run a storage file operation.

        Parameters
        ----------
        id
            The unique identifier of the bucket
        """
        return AsyncBucketProxy(id, self.session.async_client)
    

    def StorageFileAPI(self, id_: str) -> SyncBucketProxy:
        return self.from_(id_)
    
    def AsyncStorageFileAPI(self, id_: str) -> AsyncBucketProxy:
        return self.afrom_(id_)

    async def __aenter__(self) -> 'SupabaseStorageClient':
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        await self.aclose()

    async def aclose(self) -> None:
        """Close the underlying HTTP connections."""
        if self._session is not None:
            await self._session.aclose()
            self._session = None
    
    def __enter__(self) -> 'SupabaseStorageClient':
        return self
    
    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()

    def close(self) -> None:
        """Close the underlying HTTP connections."""
        if self._session is not None:
            self._session.close()
            self._session = None
    