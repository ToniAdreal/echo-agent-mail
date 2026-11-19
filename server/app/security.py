"""Password hashing (Argon2id), session tokens and CSRF helpers."""
from __future__ import annotations

import hashlib
import secrets

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

_hasher = PasswordHasher()  # Argon2id by default in argon2-cffi

# Small local denylist of widely compromised passwords (spec Section 3.3).
COMMON_PASSWORDS = {
    "password1234",
    "123456789012",
    "qwertyuiop12",
    "letmein12345",
    "admin1234567",
    "iloveyou1234",
    "password12345",
    "1234567890ab",
    "welcome12345",
    "changeme1234",
}


def hash_password(password: str) -> str:
    return _hasher.hash(password)


def verify_password(password_hash: str, password: str) -> bool:
    try:
        return _hasher.verify(password_hash, password)
    except VerifyMismatchError:
        return False
    except Exception:
        return False


def password_policy_error(password: str) -> str | None:
    if len(password) < 12:
        return "Password must be at least 12 characters long."
    if password.lower() in COMMON_PASSWORDS:
        return "This password is too common. Please choose a different one."
    return None


def new_token(nbytes: int = 32) -> str:
    return secrets.token_urlsafe(nbytes)


def sha256_hex(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()
