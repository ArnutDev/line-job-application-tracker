import base64
import hashlib
import hmac
import time
from uuid import UUID


def create_export_token(user_id: UUID, secret: str, expires_in: int = 3600) -> str:
    """Generate a tamper-proof signed token encoding user_id and expiration timestamp."""
    expires_at = int(time.time()) + expires_in
    payload = f"{user_id}:{expires_at}"
    signature = hmac.new(
        secret.encode("utf-8"),
        payload.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    raw = f"{payload}:{signature}"
    return base64.urlsafe_b64encode(raw.encode("utf-8")).decode("utf-8")


def verify_export_token(token: str, secret: str) -> UUID | None:
    """Verify the signed token's signature and expiration, returning the resolved UUID or None."""
    if not token or not secret:
        return None

    try:
        raw = base64.urlsafe_b64decode(token.encode("utf-8")).decode("utf-8")
        parts = raw.split(":")
        if len(parts) != 3:
            return None

        user_id_str, expires_at_str, signature = parts
        expires_at = int(expires_at_str)

        # Check expiration
        if time.time() > expires_at:
            return None

        payload = f"{user_id_str}:{expires_at_str}"
        expected_sig = hmac.new(
            secret.encode("utf-8"),
            payload.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

        if not hmac.compare_digest(expected_sig, signature):
            return None

        return UUID(user_id_str)
    except Exception:
        return None
