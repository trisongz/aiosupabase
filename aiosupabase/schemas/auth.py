import aiohttpx
from typing import Dict, Optional, Union, Any, Callable, List

from gotrue import (
    CookieOptions,
    SyncGoTrueAPI,
    SyncGoTrueClient,
    SyncMemoryStorage,
    SyncSupportedStorage,
    AsyncGoTrueAPI,
    AsyncGoTrueClient,
    AsyncMemoryStorage,
    AsyncSupportedStorage,
)

from gotrue.types import (
    AuthChangeEvent,
    CookieOptions,
    Provider,
    Session,
    Subscription,
    LinkType,
    User,
    UserAttributes,
    UserAttributesDict,
)

from aiosupabase.utils.config import SupabaseSettings
from aiosupabase.utils.config import settings as sb_settings
from lazyops.types import lazyproperty


class SupabaseAuthClient:

    """
    SupabaseAuthClient that wraps both
    async and sync
    """

    def __init__(
        self,
        *,
        url: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None,
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

        self.settings: SupabaseSettings = settings if settings is not None else sb_settings
        self.url = url if url is not None else self.settings.auth_url
        self.default_headers = headers if headers is not None else self.settings.default_headers
        self.auto_refresh_token = auto_refresh_token if auto_refresh_token is not None else self.settings.auto_refresh_token
        self.persist_session = persist_session if persist_session is not None else self.settings.persist_session
        self.cookie_options = cookie_options if cookie_options is not None else self.settings.cookie_options
        if isinstance(self.cookie_options, dict):
            self.cookie_options = CookieOptions.parse_obj(self.cookie_options)
        
        self.replace_default_headers = replace_default_headers if replace_default_headers is not None else self.settings.replace_default_headers

        # Lazy Initialization
        self._http_session: aiohttpx.Client = None

        self._sync_local_storage: SyncMemoryStorage = local_storage
        self._sync_api: SyncGoTrueAPI = api
        self._sync_client: SyncGoTrueClient = None

        self._async_local_storage: AsyncSupportedStorage  = async_local_storage
        self._async_api: AsyncGoTrueAPI = async_api
        self._async_client: AsyncGoTrueClient = None

    @property
    def http_session(self) -> aiohttpx.Client:
        if self._http_session is None: self._http_session = self.create_http_session()
        return self._http_session

    def create_http_session(
        self,
        base_url: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> aiohttpx.Client:
        base_url = base_url if base_url is not None else self.url
        headers = headers if headers is not None else self.headers
        return aiohttpx.Client(
            base_url = base_url,
            headers = headers,
        )


    @lazyproperty
    def headers(self):
        _headers = self.default_headers.copy()
        if self.settings.key:
            _headers["apiKey"] = self.settings.key
            _headers["Authorization"] = f"Bearer {self.settings.key}"
        return _headers

    @property
    def local_storage(self):
        if self._sync_local_storage is None:
            self._sync_local_storage = SyncMemoryStorage()
        return self._sync_local_storage
    
    @property
    def async_local_storage(self):
        if self._async_local_storage is None:
            self._async_local_storage = AsyncMemoryStorage()
        return self._async_local_storage

    @property
    def sync_api(self) -> SyncGoTrueAPI:
        if self._sync_api is None:
            self._sync_api = SyncGoTrueAPI(
                url=self.url,
                headers = self.headers,
                cookie_options = self.cookie_options,
                http_client = self.http_session.sync_client,
            )
        return self._sync_api
    
    @property
    def async_api(self) -> AsyncGoTrueAPI:
        if self._async_api is None:
            self._async_api = AsyncGoTrueAPI(
                url=self.url,
                headers = self.headers,
                cookie_options = self.cookie_options,
                http_client = self.http_session.async_client,
            )
        return self._async_api

    @property
    def client(self):
        if self._sync_client is None:
            self._sync_client = SyncGoTrueClient(
                url = self.url,
                headers = self.headers,
                auto_refresh_token = self.auto_refresh_token,
                persist_session = self.persist_session,
                cookie_options = self.cookie_options,
                replace_default_headers = self.replace_default_headers,
                local_storage = self.local_storage,
                api = self.sync_api,
            )
        return self._sync_client

    @property
    def async_client(self):
        if self._async_client is None:
            self._async_client = AsyncGoTrueClient(
                url = self.url,
                headers = self.headers,
                auto_refresh_token = self.auto_refresh_token,
                persist_session = self.persist_session,
                cookie_options = self.cookie_options,
                replace_default_headers = self.replace_default_headers,
                local_storage = self.async_local_storage,
                api = self.async_api,
            )
        return self._async_client

    """
    SyncGoTrueClient | AsyncGoTrueClient 
    Methods
    """

    def init_recover(self) -> None:
        """Recover the current session from local storage."""
        return self.client.init_recover()
    
    async def async_init_recover(self) -> None:
        """Recover the current session from local storage."""
        return await self.async_client.init_recover()
    
    def sign_up(
        self,
        *,
        email: Optional[str] = None,
        phone: Optional[str] = None,
        password: Optional[str] = None,
        redirect_to: Optional[str] = None,
        data: Optional[Dict[str, Any]] = None,
    ) -> Union[Session, User]:
        """Creates a new user. If email and phone are provided, email will be
        used and phone will be ignored.

        Parameters
        ---------
        email : Optional[str]
            The user's email address.
        phone : Optional[str]
            The user's phone number.
        password : Optional[str]
            The user's password.
        redirect_to : Optional[str]
            A URL or mobile address to send the user to after they are confirmed.
        data : Optional[Dict[str, Any]]
            Optional user metadata.

        Returns
        -------
        response : Union[Session, User]
            A logged-in session if the server has "autoconfirm" ON
            A user if the server has "autoconfirm" OFF

        Raises
        ------
        error : APIError
            If an error occurs
        """
        return self.client.sign_up(
            email=email,
            phone=phone,
            password=password,
            redirect_to=redirect_to,
            data=data,
        )

    async def async_sign_up(
        self,
        *,
        email: Optional[str] = None,
        phone: Optional[str] = None,
        password: Optional[str] = None,
        redirect_to: Optional[str] = None,
        data: Optional[Dict[str, Any]] = None,
    ) -> Union[Session, User]:
        """Creates a new user. If email and phone are provided, email will be
        used and phone will be ignored.

        Parameters
        ---------
        email : Optional[str]
            The user's email address.
        phone : Optional[str]
            The user's phone number.
        password : Optional[str]
            The user's password.
        redirect_to : Optional[str]
            A URL or mobile address to send the user to after they are confirmed.
        data : Optional[Dict[str, Any]]
            Optional user metadata.

        Returns
        -------
        response : Union[Session, User]
            A logged-in session if the server has "autoconfirm" ON
            A user if the server has "autoconfirm" OFF

        Raises
        ------
        error : APIError
            If an error occurs
        """
        return await self.async_client.sign_up(
            email=email,
            phone=phone,
            password=password,
            redirect_to=redirect_to,
            data=data,
        )

    def sign_in(
        self,
        *,
        email: Optional[str] = None,
        phone: Optional[str] = None,
        password: Optional[str] = None,
        refresh_token: Optional[str] = None,
        provider: Optional[Provider] = None,
        redirect_to: Optional[str] = None,
        scopes: Optional[str] = None,
        create_user: bool = False,
    ) -> Optional[Union[Session, str]]:
        """Log in an existing user, or login via a third-party provider.
        If email and phone are provided, email will be used and phone will be ignored.

        Parameters
        ---------
        email : Optional[str]
            The user's email address.
        phone : Optional[str]
            The user's phone number.
        password : Optional[str]
            The user's password.
        refresh_token : Optional[str]
            A valid refresh token that was returned on login.
        provider : Optional[Provider]
            One of the providers supported by GoTrue.
        redirect_to : Optional[str]
            A URL or mobile address to send the user to after they are confirmed.
        scopes : Optional[str]
            A space-separated list of scopes granted to the OAuth application.

        Returns
        -------
        response : Optional[Union[Session, str]]
            If only email are provided between the email and password,
            None is returned and send magic link to email

            If email and password are provided, a logged-in session is returned.

            If only phone are provided between the phone and password,
            None is returned and send message to phone

            If phone and password are provided, a logged-in session is returned.

            If refresh_token is provided, a logged-in session is returned.

            If provider is provided, an redirect URL is returned.

            Otherwise, error is raised.

        Raises
        ------
        error : APIError
            If an error occurs
        """
        return self.client.sign_in(
            email=email,
            phone=phone,
            password=password,
            refresh_token=refresh_token,
            provider=provider,
            redirect_to=redirect_to,
            scopes=scopes,
            create_user=create_user,
        )

    async def async_sign_in(
        self,
        *,
        email: Optional[str] = None,
        phone: Optional[str] = None,
        password: Optional[str] = None,
        refresh_token: Optional[str] = None,
        provider: Optional[Provider] = None,
        redirect_to: Optional[str] = None,
        scopes: Optional[str] = None,
        create_user: bool = False,
    ) -> Optional[Union[Session, str]]:
        """Log in an existing user, or login via a third-party provider.
        If email and phone are provided, email will be used and phone will be ignored.

        Parameters
        ---------
        email : Optional[str]
            The user's email address.
        phone : Optional[str]
            The user's phone number.
        password : Optional[str]
            The user's password.
        refresh_token : Optional[str]
            A valid refresh token that was returned on login.
        provider : Optional[Provider]
            One of the providers supported by GoTrue.
        redirect_to : Optional[str]
            A URL or mobile address to send the user to after they are confirmed.
        scopes : Optional[str]
            A space-separated list of scopes granted to the OAuth application.

        Returns
        -------
        response : Optional[Union[Session, str]]
            If only email are provided between the email and password,
            None is returned and send magic link to email

            If email and password are provided, a logged-in session is returned.

            If only phone are provided between the phone and password,
            None is returned and send message to phone

            If phone and password are provided, a logged-in session is returned.

            If refresh_token is provided, a logged-in session is returned.

            If provider is provided, an redirect URL is returned.

            Otherwise, error is raised.

        Raises
        ------
        error : APIError
            If an error occurs
        """
        return await self.async_client.sign_in(
            email=email,
            phone=phone,
            password=password,
            refresh_token=refresh_token,
            provider=provider,
            redirect_to=redirect_to,
            scopes=scopes,
            create_user=create_user,
        )

    def verify_otp(
        self,
        *,
        phone: str,
        token: str,
        redirect_to: Optional[str] = None,
    ) -> Union[Session, User]:
        """Log in a user given a User supplied OTP received via mobile.

        Parameters
        ----------
        phone : str
            The user's phone number.
        token : str
            The user's OTP.
        redirect_to : Optional[str]
            A URL or mobile address to send the user to after they are confirmed.

        Returns
        -------
        response : Union[Session, User]
            A logged-in session if the server has "autoconfirm" ON
            A user if the server has "autoconfirm" OFF

        Raises
        ------
        error : APIError
            If an error occurs
        """
        return self.client.verify_otp(
            phone=phone,
            token=token,
            redirect_to=redirect_to,
        )

    async def async_verify_otp(
        self,
        *,
        phone: str,
        token: str,
        redirect_to: Optional[str] = None,
    ) -> Union[Session, User]:
        """Log in a user given a User supplied OTP received via mobile.

        Parameters
        ----------
        phone : str
            The user's phone number.
        token : str
            The user's OTP.
        redirect_to : Optional[str]
            A URL or mobile address to send the user to after they are confirmed.

        Returns
        -------
        response : Union[Session, User]
            A logged-in session if the server has "autoconfirm" ON
            A user if the server has "autoconfirm" OFF

        Raises
        ------
        error : APIError
            If an error occurs
        """
        return await self.async_client.verify_otp(
            phone=phone,
            token=token,
            redirect_to=redirect_to,
        )

    @property
    def user(self) -> Optional[User]:
        """Returns the user data, if there is a logged in user."""
        if self._async_client: return self._async_client.user()
        return self._sync_client.user() if self._sync_client else None

    @property
    def session(self) -> Optional[Session]:
        """Returns the session data, if there is an active session."""
        if self._async_client: return self._async_client.session()
        return self._sync_client.session() if self._sync_client else None

    def refresh_session(self) -> Session:
        """Force refreshes the session.

        Force refreshes the session including the user data incase it was
        updated in a different session.
        """
        return self.client.refresh_session()
    
    async def async_refresh_session(self) -> Session:
        """Force refreshes the session.

        Force refreshes the session including the user data incase it was
        updated in a different session.
        """
        return await self.async_client.refresh_session()
    
    def update(self, *, attributes: Union[UserAttributesDict, UserAttributes]) -> User:
        """Updates user data, if there is a logged in user.

        Parameters
        ----------
        attributes : UserAttributesDict | UserAttributes
            Attributes to update, could be: email, password, email_change_token, data

        Returns
        -------
        response : User
            The updated user data.

        Raises
        ------
        error : APIError
            If an error occurs
        """
        return self.client.update(
            attributes=attributes,
        )
    
    async def async_update(self, *, attributes: Union[UserAttributesDict, UserAttributes]) -> User:
        """Updates user data, if there is a logged in user.

        Parameters
        ----------
        attributes : UserAttributesDict | UserAttributes
            Attributes to update, could be: email, password, email_change_token, data

        Returns
        -------
        response : User
            The updated user data.

        Raises
        ------
        error : APIError
            If an error occurs
        """
        return await self.async_client.update(
            attributes=attributes,
        )
    
    def set_session(self, *, refresh_token: str) -> Session:
        """Sets the session data from refresh_token and returns current Session

        Parameters
        ----------
        refresh_token : str
            A JWT token

        Returns
        -------
        response : Session
            A logged-in session

        Raises
        ------
        error : APIError
            If an error occurs
        """
        return self.client.set_session(
            refresh_token=refresh_token,
        )


    async def async_set_session(self, *, refresh_token: str) -> Session:
        """Sets the session data from refresh_token and returns current Session

        Parameters
        ----------
        refresh_token : str
            A JWT token

        Returns
        -------
        response : Session
            A logged-in session

        Raises
        ------
        error : APIError
            If an error occurs
        """
        return await self.async_client.set_session(
            refresh_token=refresh_token,
        )

    def set_auth(self, *, access_token: str) -> Session:
        """Overrides the JWT on the current client. The JWT will then be sent in
        all subsequent network requests.

        Parameters
        ----------
        access_token : str
            A JWT token

        Returns
        -------
        response : Session
            A logged-in session

        Raises
        ------
        error : APIError
            If an error occurs
        """
        return self.client.set_auth(
            access_token=access_token,
        )
    
    async def async_set_auth(self, *, access_token: str) -> Session:
        """Overrides the JWT on the current client. The JWT will then be sent in
        all subsequent network requests.

        Parameters
        ----------
        access_token : str
            A JWT token

        Returns
        -------
        response : Session
            A logged-in session

        Raises
        ------
        error : APIError
            If an error occurs
        """
        return await self.async_client.set_auth(
            access_token=access_token,
        )
    
    def get_session_from_url(
        self,
        *,
        url: str,
        store_session: bool = False,
    ) -> Session:
        """Gets the session data from a URL string.

        Parameters
        ----------
        url : str
            The URL string.
        store_session : bool
            Optionally store the session in the browser

        Returns
        -------
        response : Session
            A logged-in session

        Raises
        ------
        error : APIError
            If an error occurs
        """
        return self.client.get_session_from_url(
            url=url,
            store_session=store_session,
        )
    
    async def async_get_session_from_url(
        self,
        *,
        url: str,
        store_session: bool = False,
    ) -> Session:
        """Gets the session data from a URL string.

        Parameters
        ----------
        url : str
            The URL string.
        store_session : bool
            Optionally store the session in the browser

        Returns
        -------
        response : Session
            A logged-in session

        Raises
        ------
        error : APIError
            If an error occurs
        """
        return await self.async_client.get_session_from_url(
            url=url,
            store_session=store_session,
        )
    
    
    def sign_out(self) -> None:
        """Log the user out."""
        return self.client.sign_out()
    
    async def async_sign_out(self) -> None:
        """Log the user out."""
        return await self.async_client.sign_out()
    
    def on_auth_state_change(
        self,
        *,
        callback: Callable[[AuthChangeEvent, Optional[Session]], None],
    ) -> Subscription:
        """Receive a notification every time an auth event happens.

        Parameters
        ----------
        callback : Callable[[AuthChangeEvent, Optional[Session]], None]
            The callback to call when an auth event happens.

        Returns
        -------
        subscription : Subscription
            A subscription object which can be used to unsubscribe itself.

        Raises
        ------
        error : APIError
            If an error occurs
        """
        return self.client.on_auth_state_change(
            callback=callback,
        )
    
    async def async_on_auth_state_change(
        self,
        *,
        callback: Callable[[AuthChangeEvent, Optional[Session]], None],
     ) -> Subscription:
        """Receive a notification every time an auth event happens.

        Parameters
        ----------
        callback : Callable[[AuthChangeEvent, Optional[Session]], None]
            The callback to call when an auth event happens.

        Returns
        -------
        subscription : Subscription
            A subscription object which can be used to unsubscribe itself.

        Raises
        ------
        error : APIError
            If an error occurs
        """
        return await self.async_client.on_auth_state_change(
            callback=callback,
        )
    
    """
    AsyncGoTrueAPI / SyncGoTrueAPI
    methods
    """
    def create_user(self, *, attributes: UserAttributes) -> User:
        """Creates a new user.

        This function should only be called on a server.
        Never expose your `service_role` key in the browser.

        Parameters
        ----------
        attributes: UserAttributes
            The data you want to create the user with.

        Returns
        -------
        response : User
            The created user

        Raises
        ------
        error : APIError
            If an error occurs
        """
        return self.sync_api.create_user(
            attributes=attributes,
        )

    async def async_create_user(self, *, attributes: UserAttributes) -> User:
        """Creates a new user.

        This function should only be called on a server.
        Never expose your `service_role` key in the browser.

        Parameters
        ----------
        attributes: UserAttributes
            The data you want to create the user with.

        Returns
        -------
        response : User
            The created user

        Raises
        ------
        error : APIError
            If an error occurs
        """
        return await self.async_api.create_user(
            attributes=attributes,
        )

    def list_users(self) -> List[User]:
        """Get a list of users.

        This function should only be called on a server.
        Never expose your `service_role` key in the browser.

        Returns
        -------
        response : List[User]
            A list of users

        Raises
        ------
        error : APIError
            If an error occurs
        """
        return self.sync_api.list_users()

    async def async_list_users(self) -> List[User]:
        """Get a list of users.

        This function should only be called on a server.
        Never expose your `service_role` key in the browser.

        Returns
        -------
        response : List[User]
            A list of users

        Raises
        ------
        error : APIError
            If an error occurs
        """
        return await self.async_api.list_users()
    
    def sign_up_with_email(
        self,
        *,
        email: str,
        password: str,
        redirect_to: Optional[str] = None,
        data: Optional[Dict[str, Any]] = None,
    ) -> Union[Session, User]:
        """Creates a new user using their email address.

        Parameters
        ----------
        email : str
            The email address of the user.
        password : str
            The password of the user.
        redirect_to : Optional[str]
            A URL or mobile address to send the user to after they are confirmed.
        data : Optional[Dict[str, Any]]
            Optional user metadata.

        Returns
        -------
        response : Union[Session, User]
            A logged-in session if the server has "autoconfirm" ON
            A user if the server has "autoconfirm" OFF

        Raises
        ------
        error : APIError
            If an error occurs
        """
        return self.sync_api.sign_up_with_email(
            email=email,
            password=password,
            redirect_to=redirect_to,
            data=data,
        )

    
    async def async_sign_up_with_email(
        self,
        *,
        email: str,
        password: str,
        redirect_to: Optional[str] = None,
        data: Optional[Dict[str, Any]] = None,
    ) -> Union[Session, User]:
        """Creates a new user using their email address.

        Parameters
        ----------
        email : str
            The email address of the user.
        password : str
            The password of the user.
        redirect_to : Optional[str]
            A URL or mobile address to send the user to after they are confirmed.
        data : Optional[Dict[str, Any]]
            Optional user metadata.

        Returns
        -------
        response : Union[Session, User]
            A logged-in session if the server has "autoconfirm" ON
            A user if the server has "autoconfirm" OFF

        Raises
        ------
        error : APIError
            If an error occurs
        """
        return await self.async_api.sign_up_with_email(
            email=email,
            password=password,
            redirect_to=redirect_to,
            data=data,
        )

    def sign_in_with_email(
        self,
        *,
        email: str,
        password: str,
        redirect_to: Optional[str] = None,
    ) -> Session:
        """Logs in an existing user using their email address.

        Parameters
        ----------
        email : str
            The email address of the user.
        password : str
            The password of the user.
        redirect_to : Optional[str]
            A URL or mobile address to send the user to after they are confirmed.

        Returns
        -------
        response : Session
            A logged-in session

        Raises
        ------
        error : APIError
            If an error occurs
        """
        return self.sync_api.sign_in_with_email(
            email=email,
            password=password,
            redirect_to=redirect_to,
        )
    
    async def async_sign_in_with_email(
        self,
        *,
        email: str,
        password: str,
        redirect_to: Optional[str] = None,
    ) -> Session:
        """Logs in an existing user using their email address.

        Parameters
        ----------
        email : str
            The email address of the user.
        password : str
            The password of the user.
        redirect_to : Optional[str]
            A URL or mobile address to send the user to after they are confirmed.

        Returns
        -------
        response : Session
            A logged-in session

        Raises
        ------
        error : APIError
            If an error occurs
        """
        return await self.async_api.sign_in_with_email(
            email=email,
            password=password,
            redirect_to=redirect_to,
        )


    def sign_up_with_phone(
        self,
        *,
        phone: str,
        password: str,
        data: Optional[Dict[str, Any]] = None,
    ) -> Union[Session, User]:
        """Signs up a new user using their phone number and a password.

        Parameters
        ----------
        phone : str
            The phone number of the user.
        password : str
            The password of the user.
        data : Optional[Dict[str, Any]]
            Optional user metadata.

        Returns
        -------
        response : Union[Session, User]
            A logged-in session if the server has "autoconfirm" ON
            A user if the server has "autoconfirm" OFF

        Raises
        ------
        error : APIError
            If an error occurs
        """
        return self.sync_api.sign_up_with_phone(
            phone=phone,
            password=password,
            data=data,
        )
    
    async def async_sign_up_with_phone(
        self,
        *,
        phone: str,
        password: str,
        data: Optional[Dict[str, Any]] = None,
    ) -> Union[Session, User]:
        """Signs up a new user using their phone number and a password.

        Parameters
        ----------
        phone : str
            The phone number of the user.
        password : str
            The password of the user.
        data : Optional[Dict[str, Any]]
            Optional user metadata.

        Returns
        -------
        response : Union[Session, User]
            A logged-in session if the server has "autoconfirm" ON
            A user if the server has "autoconfirm" OFF

        Raises
        ------
        error : APIError
            If an error occurs
        """
        return await self.async_api.sign_up_with_phone(
            phone=phone,
            password=password,
            data=data,
        )

    def sign_in_with_phone(
        self,
        *,
        phone: str,
        password: str,
    ) -> Session:
        """Logs in an existing user using their phone number and password.

        Parameters
        ----------
        phone : str
            The phone number of the user.
        password : str
            The password of the user.

        Returns
        -------
        response : Session
            A logged-in session

        Raises
        ------
        error : APIError
            If an error occurs
        """
        return self.sync_api.sign_in_with_phone(
            phone=phone,
            password=password,
        )
    
    async def async_sign_in_with_phone(
        self,
        *,
        phone: str,
        password: str,
    ) -> Session:
        """Logs in an existing user using their phone number and password.

        Parameters
        ----------
        phone : str
            The phone number of the user.
        password : str
            The password of the user.

        Returns
        -------
        response : Session
            A logged-in session

        Raises
        ------
        error : APIError
            If an error occurs
        """
        return await self.async_api.sign_in_with_phone(
            phone=phone,
            password=password,
        )
    
    def send_magic_link_email(
        self,
        *,
        email: str,
        create_user: bool,
        redirect_to: Optional[str] = None,
    ) -> None:
        """Sends a magic login link to an email address.

        Parameters
        ----------
        email : str
            The email address of the user.
        redirect_to : Optional[str]
            A URL or mobile address to send the user to after they are confirmed.

        Raises
        ------
        error : APIError
            If an error occurs
        """
        return self.sync_api.send_magic_link_email(
            email=email,
            create_user=create_user,
            redirect_to=redirect_to,
        )
    
    async def async_send_magic_link_email(
        self,
        *,
        email: str,
        create_user: bool,
        redirect_to: Optional[str] = None,
    ) -> None:
        """Sends a magic login link to an email address.

        Parameters
        ----------
        email : str
            The email address of the user.
        redirect_to : Optional[str]
            A URL or mobile address to send the user to after they are confirmed.

        Raises
        ------
        error : APIError
            If an error occurs
        """
        return await self.async_api.send_magic_link_email(
            email=email,
            create_user=create_user,
            redirect_to=redirect_to,
        )

    def send_mobile_otp(self, *, phone: str, create_user: bool) -> None:
        """Sends a mobile OTP via SMS. Will register the account if it doesn't already exist

        Parameters
        ----------
        phone : str
            The user's phone number WITH international prefix

        Raises
        ------
        error : APIError
            If an error occurs
        """
        return self.sync_api.send_mobile_otp(phone=phone, create_user=create_user)

    
    async def async_send_mobile_otp(self, *, phone: str, create_user: bool) -> None:
        """Sends a mobile OTP via SMS. Will register the account if it doesn't already exist

        Parameters
        ----------
        phone : str
            The user's phone number WITH international prefix

        Raises
        ------
        error : APIError
            If an error occurs
        """
        return await self.async_api.send_mobile_otp(phone=phone, create_user=create_user)

    def verify_mobile_otp(
        self,
        *,
        phone: str,
        token: str,
        redirect_to: Optional[str] = None,
    ) -> Union[Session, User]:
        """Send User supplied Mobile OTP to be verified

        Parameters
        ----------
        phone : str
            The user's phone number WITH international prefix
        token : str
            Token that user was sent to their mobile phone
        redirect_to : Optional[str]
            A URL or mobile address to send the user to after they are confirmed.

        Returns
        -------
        response : Union[Session, User]
            A logged-in session if the server has "autoconfirm" ON
            A user if the server has "autoconfirm" OFF

        Raises
        ------
        error : APIError
            If an error occurs
        """
        return self.sync_api.verify_mobile_otp(
            phone=phone,
            token=token,
            redirect_to=redirect_to,
        )
    
    async def async_verify_mobile_otp(
        self,
        *,
        phone: str,
        token: str,
        redirect_to: Optional[str] = None,
    ) -> Union[Session, User]:
        """Send User supplied Mobile OTP to be verified

        Parameters
        ----------
        phone : str
            The user's phone number WITH international prefix
        token : str
            Token that user was sent to their mobile phone
        redirect_to : Optional[str]
            A URL or mobile address to send the user to after they are confirmed.

        Returns
        -------
        response : Union[Session, User]
            A logged-in session if the server has "autoconfirm" ON
            A user if the server has "autoconfirm" OFF

        Raises
        ------
        error : APIError
            If an error occurs
        """
        return await self.async_api.verify_mobile_otp(
            phone=phone,
            token=token,
            redirect_to=redirect_to,
        )
    
    def invite_user_by_email(
        self,
        *,
        email: str,
        redirect_to: Optional[str] = None,
        data: Optional[Dict[str, Any]] = None,
    ) -> User:
        """Sends an invite link to an email address.

        Parameters
        ----------
        email : str
            The email address of the user.
        redirect_to : Optional[str]
            A URL or mobile address to send the user to after they are confirmed.
        data : Optional[Dict[str, Any]]
            Optional user metadata.

        Returns
        -------
        response : User
            A user

        Raises
        ------
        error : APIError
            If an error occurs
        """
        return self.sync_api.invite_user_by_email(
            email=email,
            redirect_to=redirect_to,
            data=data,
        )
    
    async def async_invite_user_by_email(
        self,
        *,
        email: str,
        redirect_to: Optional[str] = None,
        data: Optional[Dict[str, Any]] = None,
    ) -> User:
        """Sends an invite link to an email address.

        Parameters
        ----------
        email : str
            The email address of the user.
        redirect_to : Optional[str]
            A URL or mobile address to send the user to after they are confirmed.
        data : Optional[Dict[str, Any]]
            Optional user metadata.

        Returns
        -------
        response : User
            A user

        Raises
        ------
        error : APIError
            If an error occurs
        """
        return await self.async_api.invite_user_by_email(
            email=email,
            redirect_to=redirect_to,
            data=data,
        )
    
    def reset_password_for_email(
        self,
        *,
        email: str,
        redirect_to: Optional[str] = None,
    ) -> None:
        """Sends a reset request to an email address.

        Parameters
        ----------
        email : str
            The email address of the user.
        redirect_to : Optional[str]
            A URL or mobile address to send the user to after they are confirmed.

        Raises
        ------
        error : APIError
            If an error occurs
        """
        return self.sync_api.reset_password_for_email(
            email=email,
            redirect_to=redirect_to,
        )
    
    async def async_reset_password_for_email(
        self,
        *,
        email: str,
        redirect_to: Optional[str] = None,
    ) -> None:
        """Sends a reset request to an email address.

        Parameters
        ----------
        email : str
            The email address of the user.
        redirect_to : Optional[str]
            A URL or mobile address to send the user to after they are confirmed.

        Raises
        ------
        error : APIError
            If an error occurs
        """
        return await self.async_api.reset_password_for_email(
            email=email,
            redirect_to=redirect_to,
        )
    
    def sign_out(self, *, jwt: str) -> None:
        """Removes a logged-in session.

        Parameters
        ----------
        jwt : str
            A valid, logged-in JWT.
        """
        return self.sync_api.sign_out(jwt=jwt)

    
    async def async_sign_out(self, *, jwt: str) -> None:
        """Removes a logged-in session.

        Parameters
        ----------
        jwt : str
            A valid, logged-in JWT.
        """
        return await self.async_api.sign_out(jwt=jwt)
    

    def get_url_for_provider(
        self,
        *,
        provider: Provider,
        redirect_to: Optional[str] = None,
        scopes: Optional[str] = None,
    ) -> str:
        """Generates the relevant login URL for a third-party provider.

        Parameters
        ----------
        provider : Provider
            One of the providers supported by GoTrue.
        redirect_to : Optional[str]
            A URL or mobile address to send the user to after they are confirmed.
        scopes : Optional[str]
            A space-separated list of scopes granted to the OAuth application.

        Returns
        -------
        url : str
            The URL to redirect the user to.

        Raises
        ------
        error : APIError
            If an error occurs
        """
        return self.sync_api.get_url_for_provider(
            provider=provider,
            redirect_to=redirect_to,
            scopes=scopes,
        )
    
    async def async_get_url_for_provider(
        self,
        *,
        provider: Provider,
        redirect_to: Optional[str] = None,
        scopes: Optional[str] = None,
    ) -> str:
        """Generates the relevant login URL for a third-party provider.

        Parameters
        ----------
        provider : Provider
            One of the providers supported by GoTrue.
        redirect_to : Optional[str]
            A URL or mobile address to send the user to after they are confirmed.
        scopes : Optional[str]
            A space-separated list of scopes granted to the OAuth application.

        Returns
        -------
        url : str
            The URL to redirect the user to.

        Raises
        ------
        error : APIError
            If an error occurs
        """
        return await self.async_api.get_url_for_provider(
            provider=provider,
            redirect_to=redirect_to,
            scopes=scopes,
        )
    
    def get_user(self, *, jwt: str) -> User:
        """Gets the user details.

        Parameters
        ----------
        jwt : str
            A valid, logged-in JWT.

        Returns
        -------
        response : User
            A user

        Raises
        ------
        error : APIError
            If an error occurs
        """
        return self.sync_api.get_user(jwt=jwt)
    
    async def async_get_user(self, *, jwt: str) -> User:
        """Gets the user details.

        Parameters
        ----------
        jwt : str
            A valid, logged-in JWT.

        Returns
        -------
        response : User
            A user

        Raises
        ------
        error : APIError
            If an error occurs
        """
        return await self.async_api.get_user(jwt=jwt)
    
    def update_user(
        self,
        *,
        jwt: str,
        attributes: UserAttributes,
    ) -> User:
        """
        Updates the user data.

        Parameters
        ----------
        jwt : str
            A valid, logged-in JWT.
        attributes : UserAttributes
            The data you want to update.

        Returns
        -------
        response : User
            A user

        Raises
        ------
        error : APIError
            If an error occurs
        """
        return self.sync_api.update_user(jwt=jwt, attributes=attributes)
    
    async def async_update_user(
        self,
        *,
        jwt: str,
        attributes: UserAttributes,
    ) -> User:
        """
        Updates the user data.

        Parameters
        ----------
        jwt : str
            A valid, logged-in JWT.
        attributes : UserAttributes
            The data you want to update.

        Returns
        -------
        response : User
            A user

        Raises
        ------
        error : APIError
            If an error occurs
        """
        return await self.async_api.update_user(jwt=jwt, attributes=attributes)

    def delete_user(self, *, uid: str, jwt: str) -> None:
        """Delete a user. Requires a `service_role` key.

        This function should only be called on a server.
        Never expose your `service_role` key in the browser.

        Parameters
        ----------
        uid : str
            The user uid you want to remove.
        jwt : str
            A valid, logged-in JWT.

        Returns
        -------
        response : User
            A user

        Raises
        ------
        error : APIError
            If an error occurs
        """
        return self.sync_api.delete_user(
            uid=uid,
            jwt=jwt,
        )
        

    async def async_delete_user(self, *, uid: str, jwt: str) -> None:
        """Delete a user. Requires a `service_role` key.

        This function should only be called on a server.
        Never expose your `service_role` key in the browser.

        Parameters
        ----------
        uid : str
            The user uid you want to remove.
        jwt : str
            A valid, logged-in JWT.

        Returns
        -------
        response : User
            A user

        Raises
        ------
        error : APIError
            If an error occurs
        """
        return await self.async_api.delete_user(
            uid=uid,
            jwt=jwt,
        )

    def refresh_access_token(self, *, refresh_token: str) -> Session:
        """Generates a new JWT.

        Parameters
        ----------
        refresh_token : str
            A valid refresh token that was returned on login.

        Returns
        -------
        response : Session
            A session

        Raises
        ------
        error : APIError
            If an error occurs
        """
        return self.sync_api.refresh_access_token(
            refresh_token=refresh_token,
        )

    async def async_refresh_access_token(self, *, refresh_token: str) -> Session:
        """Generates a new JWT.

        Parameters
        ----------
        refresh_token : str
            A valid refresh token that was returned on login.

        Returns
        -------
        response : Session
            A session

        Raises
        ------
        error : APIError
            If an error occurs
        """
        return await self.async_api.refresh_access_token(
            refresh_token=refresh_token,
        )

    def generate_link(
        self,
        *,
        type: LinkType,
        email: str,
        password: Optional[str] = None,
        redirect_to: Optional[str] = None,
        data: Optional[Dict[str, Any]] = None,
    ) -> Union[Session, User]:
        """
        Generates links to be sent via email or other.

        Parameters
        ----------
        type : LinkType
            The link type ("signup" or "magiclink" or "recovery" or "invite").
        email : str
            The user's email.
        password : Optional[str]
            User password. For signup only.
        redirect_to : Optional[str]
            The link type ("signup" or "magiclink" or "recovery" or "invite").
        data : Optional[Dict[str, Any]]
            Optional user metadata. For signup only.

        Returns
        -------
        response : Union[Session, User]
            A logged-in session if the server has "autoconfirm" ON
            A user if the server has "autoconfirm" OFF

        Raises
        ------
        error : APIError
            If an error occurs
        """
        return self.sync_api.generate_link(
            type=type,
            email=email,
            password=password,
            redirect_to=redirect_to,
            data=data,
        )

    async def async_generate_link(
        self,
        *,
        type: LinkType,
        email: str,
        password: Optional[str] = None,
        redirect_to: Optional[str] = None,
        data: Optional[Dict[str, Any]] = None,
    ) -> Union[Session, User]:
        """
        Generates links to be sent via email or other.

        Parameters
        ----------
        type : LinkType
            The link type ("signup" or "magiclink" or "recovery" or "invite").
        email : str
            The user's email.
        password : Optional[str]
            User password. For signup only.
        redirect_to : Optional[str]
            The link type ("signup" or "magiclink" or "recovery" or "invite").
        data : Optional[Dict[str, Any]]
            Optional user metadata. For signup only.

        Returns
        -------
        response : Union[Session, User]
            A logged-in session if the server has "autoconfirm" ON
            A user if the server has "autoconfirm" OFF

        Raises
        ------
        error : APIError
            If an error occurs
        """
        return await self.async_api.generate_link(
            type=type,
            email=email,
            password=password,
            redirect_to=redirect_to,
            data=data,
        )


    def unsubscribe(self, *, id: str) -> None:
        """Unsubscribe from a subscription."""
        return self.client._unsubscribe(id=id)
    
    async def async_unsubscribe(self, *, id: str) -> None:
        """Unsubscribe from a subscription."""
        return await self.async_client._unsubscribe(id=id)
    

    def __enter__(self):
        return self

    def __exit__(self, exc_t, exc_v, exc_tb) -> None:
        self.close()

    def close(self) -> None:
        self.client.close()
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_t, exc_v, exc_tb) -> None:
        await self.aclose()
    
    async def aclose(self):
        await self.async_client.close()