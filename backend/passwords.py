"""One password function for signup and login.

Stored form, matching the rows already in users:
    pbkdf2_sha256$<salt>$<hex digest>

Login reads the salt from that string. It does not create a new salt,
and it does not reverse the stored digest.
"""

import hashlib
import hmac
import secrets

ALGORITHM = "pbkdf2_sha256"
HASH_NAME = "sha256"
ITERATIONS = 600_000
DIGEST_BYTES = 32


def hash_password(password: str, salt: str | None = None) -> str:
    """Hash a password. A missing salt means signup; a provided salt means login."""
    if salt is None:
        salt = secrets.token_hex(8)
    digest = hashlib.pbkdf2_hmac(
        HASH_NAME,
        password.encode("utf-8"),
        salt.encode("utf-8"),
        ITERATIONS,
        dklen=DIGEST_BYTES,
    )
    return f"{ALGORITHM}${salt}${digest.hex()}"


def verify_password(password: str, stored: str) -> bool:
    """Re-hash the typed password with the stored salt and compare digests."""
    try:
        algorithm, salt, stored_digest = _split(stored)
    except ValueError:
        return False
    if algorithm != ALGORITHM or not salt or not stored_digest:
        return False
    _, _, typed_digest = _split(hash_password(password, salt))
    return hmac.compare_digest(typed_digest, stored_digest)


def _split(stored: str) -> tuple[str, str, str]:
    algorithm, salt, digest = stored.split("$")
    return algorithm, salt, digest
