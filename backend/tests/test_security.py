from __future__ import annotations

import pytest

from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)


def test_password_hash_and_verify_roundtrip() -> None:
    password = "correct horse battery staple"
    hashed_password = hash_password(password)

    assert hashed_password != password
    assert verify_password(password, hashed_password) is True
    assert verify_password("wrong-password", hashed_password) is False


def test_access_token_roundtrip() -> None:
    token = create_access_token(subject="42")
    payload = decode_token(token)

    assert payload["sub"] == "42"
    assert payload["type"] == "access"
    assert "exp" in payload


def test_refresh_token_roundtrip() -> None:
    token = create_refresh_token(subject="84")
    payload = decode_token(token)

    assert payload["sub"] == "84"
    assert payload["type"] == "refresh"
    assert "exp" in payload


def test_decode_invalid_token_raises_value_error() -> None:
    with pytest.raises(ValueError):
        decode_token("not-a-real-token")
