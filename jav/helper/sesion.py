# i forgot where i got this code inspiration. please tell me if you know

import functools
from http.cookiejar import LWPCookieJar

from httpx import AsyncClient, Client, Timeout
from urllib3.util import parse_url

from . import header, sessions_cache

METH_ALL = ("GET", "OPTIONS", "HEAD", "POST", "PUT", "PATCH", "DELETE")


class NetRequests:
    def __init__(self, timeout: int = 10):
        self._timeout = Timeout(timeout=timeout)

    @staticmethod
    def _isactive_session(host: str) -> bool:
        return not sessions_cache[host].is_closed

    def _create_session(self, host: str) -> Client:
        sessions_cache[host] = Client(timeout=self._timeout)
        sessions_cache[host].headers["User-Agent"] = header
        sessions_cache[host].cookies = LWPCookieJar()
        return sessions_cache[host]

    def _get_session(self, url: str) -> Client:
        host = parse_url(url).host
        if host in sessions_cache and self._isactive_session(host):
            return sessions_cache[host]

        return self._create_session(host)

    def __getattr__(self, attr):
        if attr.upper() in METH_ALL:

            def get_sessions(session):
                @functools.wraps(session)
                def session_request(url, **kwargs):
                    return session(url).request(attr.upper(), url, **kwargs)

                return session_request

            return get_sessions(self._get_session)

        raise AttributeError(
            f"[attribute not found] wrong atribute detected : ({attr})"
        )


class AsyncNetRequests:
    def __init__(self, timeout: int = 20):
        self._timeout = Timeout(timeout=timeout)

    @staticmethod
    def _isactive_session(host: str) -> bool:
        return not sessions_cache[host].is_closed

    def _create_session(self, host: str):
        sessions_cache[host] = AsyncClient(timeout=self._timeout)
        sessions_cache[host].headers["User-Agent"] = header
        sessions_cache[host].cookies = LWPCookieJar()
        return sessions_cache[host]

    def _get_session(self, url: str):
        host = parse_url(url).host
        if host in sessions_cache and self._isactive_session(host):
            return sessions_cache[host]

        return self._create_session(host)

    def __getattr__(self, attr):
        if attr.upper() in METH_ALL:

            def get_sessions(session):
                @functools.wraps(session)
                def session_request(url, **kwargs):
                    return session(url).request(attr.upper(), url, **kwargs)

                return session_request

            return get_sessions(self._get_session)

        # return super().__getattribute__(attr)
        raise AttributeError(
            f"[attribute not found] wrong atribute detected : ({attr})"
        )
