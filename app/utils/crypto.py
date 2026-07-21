from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend
from base64 import urlsafe_b64encode
from typing import Optional

from ..core import settings


def _derive_key_from_passphrase(passphrase: str, salt: bytes) -> bytes:
    # derive a 32-byte key and return urlsafe base64 encoded bytes for Fernet
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=390000,
        backend=default_backend(),
    )
    return urlsafe_b64encode(kdf.derive(passphrase.encode()))


def _get_fernet() -> Fernet:
    key = settings.ENCRYPTION_KEY
    if not key:
        raise RuntimeError("ENCRYPTION_KEY not configured in settings")

    # If key already looks like a Fernet key (44 urlsafe-base64 chars), use it
    if isinstance(key, str) and len(key) == 44:
        try:
            return Fernet(key.encode())
        except Exception:
            pass

    # Otherwise treat the value as a passphrase and derive a Fernet key
    # Use SECRET_KEY (if available) as salt; fallback to a fixed salt.
    salt_source: Optional[str] = settings.SECRET_KEY or "fastapi-mfa-salt"
    salt = salt_source.encode()[:16].ljust(16, b"0")
    derived = _derive_key_from_passphrase(key, salt)
    return Fernet(derived)


def encrypt_secret(secret: str) -> str:
    f = _get_fernet()
    return f.encrypt(secret.encode()).decode()


def decrypt_secret(token: str) -> str:
    f = _get_fernet()
    try:
        return f.decrypt(token.encode()).decode()
    except InvalidToken:
        raise RuntimeError("Invalid encryption token")
