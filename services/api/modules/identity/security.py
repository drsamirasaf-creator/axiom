"""Password hashing and session tokens (ADR-007). REQ-IDN-002.

scrypt (stdlib, memory-hard) with per-user 16-byte salt; format
'scrypt$<salt hex>$<hash hex>'. Constant-time comparison throughout.
No external crypto dependencies to pin or patch.
"""
import hashlib
import hmac
import secrets

_N, _R, _P = 2 ** 14, 8, 1
MIN_PASSWORD_LEN = 10
SESSION_DAYS = 30


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    h = hashlib.scrypt(password.encode(), salt=salt, n=_N, r=_R, p=_P)
    return f"scrypt${salt.hex()}${h.hex()}"


def verify_password(password: str, stored: str) -> bool:
    try:
        scheme, salt_hex, hash_hex = stored.split("$")
        if scheme != "scrypt":
            return False
        h = hashlib.scrypt(password.encode(), salt=bytes.fromhex(salt_hex),
                           n=_N, r=_R, p=_P)
        return hmac.compare_digest(h.hex(), hash_hex)
    except (ValueError, TypeError):
        return False


def new_session_token() -> str:
    return secrets.token_urlsafe(32)


def token_hash(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def new_tenant() -> str:
    return "u-" + secrets.token_hex(8)
