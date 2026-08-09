"""Password hashing and token handling."""

from __future__ import annotations

import time

import jwt
import pytest

from app.core.config import settings
from app.core.security import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)


def test_hashes_are_salted_so_equal_passwords_differ():
    assert hash_password("Password123!") != hash_password("Password123!")


def test_verify_accepts_the_correct_password():
    assert verify_password("Password123!", hash_password("Password123!"))


def test_verify_rejects_a_wrong_password():
    assert not verify_password("wrong", hash_password("Password123!"))


def test_verify_rejects_a_malformed_hash():
    assert not verify_password("Password123!", "not-a-hash")


def test_empty_passwords_are_refused():
    with pytest.raises(ValueError):
        hash_password("")


def test_production_default_uses_a_costly_kdf():
    assert type(settings).model_fields["password_hash_iterations"].default >= 210_000


def test_token_round_trip_carries_the_subject():
    token = create_access_token(42, {"org": 7})

    claims = decode_access_token(token)

    assert claims["sub"] == "42"
    assert claims["org"] == 7


def test_a_tampered_token_is_rejected():
    token = create_access_token(42)

    with pytest.raises(jwt.PyJWTError):
        decode_access_token(token[:-2] + ("ab" if not token.endswith("ab") else "cd"))


def test_an_expired_token_is_rejected(monkeypatch):
    monkeypatch.setattr(settings, "access_token_expire_minutes", -1)
    token = create_access_token(42)
    time.sleep(0.01)

    with pytest.raises(jwt.ExpiredSignatureError):
        decode_access_token(token)
