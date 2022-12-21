import aiohttpx

from typing import Dict, Optional
from aiosupabase.utils.config import SupabaseSettings
from aiosupabase.utils.config import settings as sb_settings
from lazyops.types import lazyproperty



class FunctionsClient:
    def __init__(
        self, 
        url: Optional[str] = None,
        headers: Optional[Dict] = None,
        settings: Optional[SupabaseSettings] = None,
    ):
        self.settings = settings if settings is None else sb_settings
        self.url = url if url is not None else self.settings.functions_url
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

    def set_auth(self, token: str) -> None:
        """Updates the authorization header

        Parameters
        ----------
        token : str
            the new jwt token sent in the authorisation header
        """
        if self._session:
            self.session.headers["Authorization"] = f"Bearer {token}"
        else:
            self.default_headers["Authorization"] = f"Bearer {token}"
        

    def invoke(self, function_name: str, invoke_options: Dict) -> Dict:
        """Invokes a function

        Parameters
        ----------
        function_name : the name of the function to invoke
        invoke_options : object with the following properties
            `headers`: object representing the headers to send with the request
            `body`: the body of the request
            `responseType`: how the response should be parsed. The default is `json`

        Returns
        -------
        Dict
            Dictionary with data and/or error message
        """
        try:
            headers = {**self.headers, **invoke_options.get('headers', {})}
            body = invoke_options.get('body')
            response_type = invoke_options.get('responseType')
            response = self.session.post(
                f"{self.url}/{function_name}", headers=headers, json=body)
            is_relay_error = response.headers.get('x-relay-header')
            if is_relay_error and is_relay_error == 'true':
                return {
                    "data": None,
                    "error": response.text
                }
            data = response.json() if response_type == 'json' else response.content
            return {"data": data, "error": None}
        except Exception as e:
            return {
                "data": None,
                "error": e
            }


    async def async_invoke(self, function_name: str, invoke_options: Dict) -> Dict:
        """Invokes a function

        Parameters
        ----------
        function_name : the name of the function to invoke
        invoke_options : object with the following properties
            `headers`: object representing the headers to send with the request
            `body`: the body of the request
            `responseType`: how the response should be parsed. The default is `json`

        Returns
        -------
        Dict
            Dictionary with data and/or error message
        """
        try:
            headers = {**self.headers, **invoke_options.get('headers', {})}
            body = invoke_options.get('body')
            response_type = invoke_options.get('responseType')
            response = await self.session.async_post(
                f"{self.url}/{function_name}", headers=headers, json=body)
            is_relay_error = response.headers.get('x-relay-header')
            if is_relay_error and is_relay_error == 'true':
                return {
                    "data": None,
                    "error": response.text
                }
            data = response.json() if response_type == 'json' else response.content
            return {"data": data, "error": None}
        except Exception as e:
            return {
                "data": None,
                "error": e
            }

    
    async def __aenter__(self) -> 'FunctionsClient':
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        await self.aclose()

    async def aclose(self) -> None:
        """Close the underlying HTTP connections."""
        if self._session is not None:
            await self._session.aclose()
            self._session = None
    
    def __enter__(self) -> 'FunctionsClient':
        return self
    
    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()

    def close(self) -> None:
        """Close the underlying HTTP connections."""
        if self._session is not None:
            self._session.close()
            self._session = None
    