"""Telegram WebApp initData verification.

Telegram signs initData with HMAC-SHA256 using
secret = HMAC_SHA256(key="WebAppData", msg=BOT_TOKEN)

We verify this signature on every API call from the WebApp.
See: https://core.telegram.org/bots/webapps#validating-data-received-via-the-mini-app
"""
import hmac
import hashlib
import json
import time
from urllib.parse import parse_qsl
from app.config import get_settings

# Reject initData older than this (Telegram spec: data should be fresh).
MAX_INIT_DATA_AGE = 24 * 3600  # 24h


def verify_init_data(init_data: str) -> dict:
    """Verify signature + freshness, return parsed dict including 'user'.

    Returns a dict with keys from initData, where 'user' is already
    parsed from JSON. Raises ValueError on failure.
    """
    if not init_data:
        raise ValueError("empty_init_data")

    settings = get_settings()
    pairs = dict(parse_qsl(init_data, strict_parsing=True))
    received_hash = pairs.pop("hash", None)
    if not received_hash:
        raise ValueError("missing_hash")

    data_check_string = "\n".join(
        f"{k}={v}" for k, v in sorted(pairs.items())
    )
    secret_key = hmac.new(
        b"WebAppData", settings.bot_token.encode(), hashlib.sha256
    ).digest()
    calculated = hmac.new(
        secret_key, data_check_string.encode(), hashlib.sha256
    ).hexdigest()

    if not hmac.compare_digest(calculated, received_hash):
        raise ValueError("bad_signature")

    # Freshness check
    auth_date = pairs.get("auth_date")
    if auth_date and time.time() - int(auth_date) > MAX_INIT_DATA_AGE:
        raise ValueError("stale_init_data")

    # Parse nested user JSON
    if "user" in pairs:
        try:
            pairs["user"] = json.loads(pairs["user"])
        except json.JSONDecodeError:
            raise ValueError("bad_user_json")

    return pairs
