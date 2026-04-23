"""QR token encoding/decoding with HMAC signature and TTL.

A QR token is `base64url(user_id . timestamp . hmac_sig)`.
We verify the signature and expiry — no DB lookup required to validate.
"""
import base64
import hmac
import hashlib
import time
from app.config import get_settings

_TTL_SECONDS = 365 * 24 * 3600  # 1 year


def _secret() -> bytes:
    return get_settings().qr_secret.encode()


def _b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _b64url_decode(data: str) -> bytes:
    padding = "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode(data + padding)


def qr_encode(user_id: str) -> str:
    """Create a signed QR token for a user.

    The same user always gets the same token per timestamp. For fresh rotation,
    call this again and persist the new value in users.qr_token.
    """
    ts = int(time.time())
    payload = f"{user_id}.{ts}".encode("ascii")
    sig = hmac.new(_secret(), payload, hashlib.sha256).digest()[:16]
    return _b64url(payload + b"." + sig)


def qr_decode(token: str) -> str:
    """Verify HMAC signature + expiry, return user_id.

    Raises ValueError on any failure.
    """
    try:
        raw = _b64url_decode(token)
    except Exception as e:
        raise ValueError("malformed_token") from e

    try:
        payload, sig = raw.rsplit(b".", 1)
    except ValueError:
        raise ValueError("malformed_token")

    expected = hmac.new(_secret(), payload, hashlib.sha256).digest()[:16]
    if not hmac.compare_digest(sig, expected):
        raise ValueError("invalid_signature")

    try:
        user_id, ts_str = payload.decode("ascii").split(".")
        ts = int(ts_str)
    except Exception as e:
        raise ValueError("malformed_payload") from e

    if time.time() - ts > _TTL_SECONDS:
        raise ValueError("expired")

    return user_id
