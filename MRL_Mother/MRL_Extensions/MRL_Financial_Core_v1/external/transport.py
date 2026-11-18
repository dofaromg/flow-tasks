"""Bounded HTTPS JSON transport; no redirects, retries or exception data leaks."""

import json
from decimal import Decimal
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener

from ..core import Rejected, require


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def https_url(url):
    """Accept a configured HTTPS origin/path without URL credentials or query keys."""
    require(isinstance(url, str) and not any(c.isspace() for c in url), "INVALID_ENDPOINT")
    try:
        parsed = urlsplit(url)
        port = parsed.port
    except ValueError as exc:
        raise Rejected("INVALID_ENDPOINT") from exc
    require(parsed.scheme == "https" and parsed.hostname and
            not parsed.username and not parsed.password and not parsed.query and
            not parsed.fragment and (port is None or 0 < port < 65536), "HTTPS_ENDPOINT_REQUIRED")
    return url


class JsonTransport:
    """Use inherited proxy/CA settings. Provider bodies and tokens never enter errors."""

    def __init__(self):
        self.opener = build_opener(NoRedirect())

    def request(self, method, url, body=None, headers=None):
        https_url(url)
        request = Request(url, data=body, method=method,
                          headers={"Accept": "application/json", "Content-Type": "application/json",
                                   **(headers or {})})
        try:
            with self.opener.open(request, timeout=20) as response:
                raw = response.read(1024 * 1024 + 1)
                require(len(raw) <= 1024 * 1024, "PROVIDER_RESPONSE_TOO_LARGE")
                require(200 <= response.status < 300, "PROVIDER_HTTP_FAILURE")
            return json.loads(raw, parse_float=Decimal)
        except HTTPError as exc:
            exc.close()
            raise Rejected(f"PROVIDER_HTTP_{exc.code}") from None
        except (URLError, OSError, ValueError) as exc:
            raise Rejected("PROVIDER_RESPONSE_UNAVAILABLE") from None
