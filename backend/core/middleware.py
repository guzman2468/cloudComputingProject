"""Reusable request middleware for application-wide security checks."""

from urllib.parse import unquote

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import PlainTextResponse, Response


def contains_path_traversal(raw_path: bytes) -> bool:
    """Detect dot-dot traversal, including encoded slash/backslash variants."""
    try:
        path = raw_path.decode("utf-8", errors="strict")
    except UnicodeDecodeError:
        return True

    # Decode twice to catch values such as %252e%252e%252f.
    for _ in range(2):
        path = unquote(path)

    path = path.replace("\\", "/")
    return "\x00" in path or any(segment == ".." for segment in path.split("/"))


class PathTraversalMiddleware(BaseHTTPMiddleware):
    """Reject traversal attempts before they reach any current or future route."""

    async def dispatch(self, request: Request, call_next) -> Response:
        if contains_path_traversal(request.scope.get("raw_path", b"")):
            return PlainTextResponse("Not Found", status_code=404)
        return await call_next(request)
