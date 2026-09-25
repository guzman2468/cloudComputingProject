"""Simple process-local rate limiting for the single-container deployment."""

from collections import defaultdict, deque
from threading import Lock
from time import monotonic

from fastapi import HTTPException, Request, status

from backend.core.security import SESSION_COOKIE, get_session_email


class InMemoryRateLimiter:
    def __init__(self) -> None:
        self._events: dict[str, deque[float]] = defaultdict(deque)
        self._lock = Lock()

    def check(self, key: str, limit: int, window_seconds: int) -> None:
        now = monotonic()
        cutoff = now - window_seconds
        with self._lock:
            events = self._events[key]
            while events and events[0] <= cutoff:
                events.popleft()
            if len(events) >= limit:
                retry_after = max(1, int(events[0] + window_seconds - now))
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Too many requests. Please try again later.",
                    headers={"Retry-After": str(retry_after)},
                )
            events.append(now)

    def active_count(self, prefix: str) -> int:
        with self._lock:
            return sum(1 for key in self._events if key.startswith(prefix))


rate_limiter = InMemoryRateLimiter()


def _client_ip(request: Request) -> str:
    # request.client is the only address trusted here. Forwarded headers should
    # only be used after configuring a trusted reverse proxy.
    return request.client.host if request.client else "unknown"


def _user_key(request: Request) -> str:
    email = get_session_email(request.cookies.get(SESSION_COOKIE))
    return email.lower() if email else f"ip:{_client_ip(request)}"


def _check(request: Request, name: str, limit: int, window_seconds: int, suffix: str = "") -> None:
    rate_limiter.check(f"{name}:{_user_key(request)}{suffix}", limit, window_seconds)


def registration_rate_limit(request: Request) -> None:
    rate_limiter.check(f"registration:ip:{_client_ip(request)}", 10, 60 * 60)


def login_rate_limit(request: Request, email: str | None = None) -> None:
    rate_limiter.check(f"login:ip:{_client_ip(request)}", 5, 60)
    if email:
        rate_limiter.check(f"login:email:{email.strip().lower()}", 5, 60)


def user_search_rate_limit(request: Request) -> None:
    _check(request, "user-search", 60, 60)


def room_read_rate_limit(request: Request) -> None:
    _check(request, "room-read", 60, 60)


def room_search_rate_limit(request: Request) -> None:
    _check(request, "room-search", 60, 60)


def room_create_rate_limit(request: Request) -> None:
    _check(request, "room-create", 20, 60 * 60)


def room_mutation_rate_limit(request: Request) -> None:
    _check(request, "room-mutation", 30, 60 * 60)


def message_read_rate_limit(request: Request, room_id: int) -> None:
    _check(request, "message-read", 60, 60, f":room:{room_id}")


def message_send_rate_limit(request: Request, room_id: int) -> None:
    _check(request, "message-send", 30, 60, f":room:{room_id}")
    _check(request, "message-send-total", 60, 60)


def websocket_ip_rate_limit(request: Request) -> None:
    rate_limiter.check(f"websocket:ip:{_client_ip(request)}", 5, 60)
