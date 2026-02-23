"""
Validate slack requests
"""

from fastapi import Request
import time
import hmac
import hashlib


async def validate(request: Request, signing_secret: str) -> bool:
    """Validate incoming Slack request using the signing secret."""

    timestamp = request.headers.get("X-Slack-Request-Timestamp")
    slack_signature = request.headers.get("X-Slack-Signature")

    if not timestamp or not slack_signature:
        return False

    if abs(time.time() - int(timestamp)) > 300:
        return False

    body = await request.body()
    sig_basestring = f"v0:{timestamp}:{body.decode()}"
    my_signature = f"v0={hmac.new(signing_secret.encode(), sig_basestring.encode(), hashlib.sha256).hexdigest()}"

    return hmac.compare_digest(my_signature, slack_signature)
