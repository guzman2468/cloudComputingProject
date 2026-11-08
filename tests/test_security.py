"""Unit tests for password hashing and session tokens."""

from backend.core.security import (
    create_session_token,
    get_session_email,
    hash_password,
    verify_password,
)


def test_hash_password_format():
    hashed = hash_password("SuperSecret123!")
    assert hashed.startswith("scrypt$")
    parts = hashed.split("$")
    assert len(parts) == 3
    assert len(parts[1]) > 0  # salt
    assert len(parts[2]) > 0  # digest


def test_verify_password_success():
    password = "CorrectHorseBatteryStaple!"
    hashed = hash_password(password)
    assert verify_password(password, hashed) is True


def test_verify_password_failure():
    hashed = hash_password("MySecretPassword99#")
    assert verify_password("WrongPassword123!", hashed) is False
    assert verify_password("", hashed) is False


def test_unique_salts_for_same_password():
    pwd = "IdenticalPassword123"
    hash1 = hash_password(pwd)
    hash2 = hash_password(pwd)
    assert hash1 != hash2
    assert verify_password(pwd, hash1) is True
    assert verify_password(pwd, hash2) is True


def test_session_token_roundtrip():
    email = "talon@unomaha.edu"
    token = create_session_token(email)
    assert token is not None
    recovered_email = get_session_email(token)
    assert recovered_email == email


def test_session_token_tampered():
    email = "talon@unomaha.edu"
    token = create_session_token(email)
    payload, sig = token.split(".", 1)
    tampered_token = f"{payload}.tampered_signature"
    assert get_session_email(tampered_token) is None
    assert get_session_email("invalid_token") is None
    assert get_session_email(None) is None

