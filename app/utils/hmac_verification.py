import os
import hmac
import hashlib
import base64
from fastapi import Request, HTTPException, status


async def verify_shopify_webhook(request: Request) -> None:
    """
    Verify that the webhook request came from Shopify

    Args:
        request: The FastAPI request object

    Raises:
        HTTPException: If the webhook signature is invalid
    """
    webhook_secret = os.environ.get("SHOPIFY_WEBHOOK_SECRET")
    if not webhook_secret:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="SHOPIFY_WEBHOOK_SECRET not configured"
        )

    # Get the HMAC header
    hmac_header = request.headers.get("X-Shopify-Hmac-SHA256")
    if not hmac_header:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing HMAC signature"
        )

    # Get the request body
    body = await request.body()

    # Calculate HMAC
    calculated_hmac = base64.b64encode(
        hmac.new(
            key=webhook_secret.encode(),
            msg=body,
            digestmod=hashlib.sha256
        ).digest()
    ).decode()

    # Compare calculated HMAC with header value
    if not hmac.compare_digest(calculated_hmac, hmac_header):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid HMAC signature"
        )
