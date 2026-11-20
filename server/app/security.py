"""Password hashing (Argon2id), session tokens, CSRF helpers and secret
encryption for stored provider tokens (OAuth access/refresh tokens, PKCE
verifiers)."""
from __future__ import annotations

import base64
import hashlib
import secrets

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from cryptography.fernet import Fernet

from .config import settings

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


# ---------------------------------------------------------------------------
# Secret encryption (Fernet). The key is derived from TOKEN_ENCRYPTION_KEY,
# falling back to SESSION_SECRET, so existing deployments keep working with
# the secret they already run with. decrypt_secret tolerates legacy rows
# written before encryption existed: anything that is not a valid Fernet
# token is returned unchanged.
# ---------------------------------------------------------------------------


def _fernet() -> Fernet:
    material = settings.TOKEN_ENCRYPTION_KEY or settings.SESSION_SECRET
    key = base64.urlsafe_b64encode(hashlib.sha256(material.encode("utf-8")).digest())
    return Fernet(key)


def encrypt_secret(plaintext: str) -> str:
    return _fernet().encrypt(plaintext.encode("utf-8")).decode("ascii")


def decrypt_secret(value: str) -> str:
    if not value:
        return value
    try:
        return _fernet().decrypt(value.encode("utf-8")).decode("utf-8")
    except Exception:
        # Pre-encryption (plaintext) row or a value encrypted under another
        # key: hand back the stored value rather than failing the flow.
        return value
