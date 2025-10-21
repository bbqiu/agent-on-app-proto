import contextvars
from typing import Dict, Optional

_request_headers: contextvars.ContextVar[Dict[str, str]] = contextvars.ContextVar(
    "request_headers", default={}
)


def set_request_headers(headers: Dict[str, str]) -> None:
    """Set request headers in the current context (called by server)"""
    _request_headers.set(headers)


def get_request_headers() -> Dict[str, str]:
    """Get all request headers from the current context"""
    return _request_headers.get()


def get_header(name: str, default: Optional[str] = None) -> Optional[str]:
    """Get a specific header value from the current context"""
    return get_request_headers().get(name, default)


def get_forwarded_access_token() -> Optional[str]:
    """Get the x-forwarded-access-token from the current request context"""
    return get_header("x-forwarded-access-token")
