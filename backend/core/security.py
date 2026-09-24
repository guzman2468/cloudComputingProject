"""Security helpers used by authentication services."""

import base64
import hashlib
import hmac
import json
import os
import time


SESSION_COOKIE = "mavchat_session"
SESSION_MAX_AGE = 60 * 60
SESSION_SECRET = os.getenv("SESSION_SECRET", "development-secret-change-me").encode("utf-8")


def hash_password(password: str) -> str:
    """Return a salted, one-way password hash suitable for database storage."""
    salt = os.urandom(16)
    digest = hashlib.scrypt(password.encode("utf-8"), salt=salt, n=2**14, r=8, p=1)
    return "scrypt${}${}".format(
        base64.urlsafe_b64encode(salt).decode("ascii"),
        base64.urlsafe_b64encode(digest).decode("ascii"),
    )


def verify_password(password: str, stored_hash: str) -> bool:
    """Verify a password against a hash produced by :func:`hash_password`."""
    try:
        algorithm, encoded_salt, encoded_digest = stored_hash.split("$", 2)
        if algorithm != "scrypt":
            return False
        salt = base64.urlsafe_b64decode(encoded_salt.encode("ascii"))
        expected = base64.urlsafe_b64decode(encoded_digest.encode("ascii"))
        actual = hashlib.scrypt(password.encode("utf-8"), salt=salt, n=2**14, r=8, p=1)
        return hmac.compare_digest(actual, expected)
    except (ValueError, TypeError):
        return False


def create_session_token(email: str) -> str:
    payload = json.dumps(
        {"email": email, "expires": int(time.time()) + SESSION_MAX_AGE},
        separators=(",", ":"),
    ).encode("utf-8")
    encoded_payload = base64.urlsafe_b64encode(payload).decode("ascii")
    signature = hmac.new(SESSION_SECRET, encoded_payload.encode("ascii"), hashlib.sha256).digest()
    encoded_signature = base64.urlsafe_b64encode(signature).decode("ascii")
    return f"{encoded_payload}.{encoded_signature}"


def get_session_email(token: str | None) -> str | None:
    if not token or "." not in token:
        return None

    encoded_payload, encoded_signature = token.split(".", 1)
    expected_signature = hmac.new(
        SESSION_SECRET, encoded_payload.encode("ascii"), hashlib.sha256
    ).digest()
    try:
        supplied_signature = base64.urlsafe_b64decode(encoded_signature.encode("ascii"))
        payload = json.loads(base64.urlsafe_b64decode(encoded_payload.encode("ascii")))
    except (ValueError, TypeError, json.JSONDecodeError):
        return None

    if not hmac.compare_digest(supplied_signature, expected_signature):
        return None
    if payload.get("expires", 0) < time.time():
        return None
    return payload.get("email")
