"""
HMAC Signature Utilities for Webhook Security
Feature: 002-remote-persistence-safety
Task: T014

Provides HMAC-SHA256 signature generation and validation for webhook security.
Used to authenticate webhook requests between local API and n8n.
"""

import hashlib
import hmac
import os
from typing import Union

from fastapi import Request, HTTPException, status


def generate_signature(payload: bytes, secret: str) -> str:
    """
    Generate HMAC-SHA256 signature for a payload.

    Args:
        payload: The raw bytes of the request body
        secret: The shared secret token (MEMORY_WEBHOOK_TOKEN)

    Returns:
        Signature string in format "sha256=<hex_digest>"

    Example:
        >>> payload = b'{"memory_id": "123"}'
        >>> secret = "my-secret-token"
        >>> sig = generate_signature(payload, secret)
        >>> sig.startswith("sha256=")
        True
    """
    digest = hmac.new(
        key=secret.encode("utf-8"),
        msg=payload,
        digestmod=hashlib.sha256,
    ).hexdigest()

    return f"sha256={digest}"


def validate_signature(
    payload: bytes,
    signature: Union[str, None],
    secret: str,
) -> bool:
    """
    Validate HMAC-SHA256 signature using timing-safe comparison.

    Args:
        payload: The raw bytes of the request body
        signature: The signature from X-Webhook-Signature header
        secret: The shared secret token (MEMORY_WEBHOOK_TOKEN)

    Returns:
        True if signature is valid, False otherwise

    Security:
        Uses hmac.compare_digest for constant-time comparison
        to prevent timing attacks.

    Example:
        >>> payload = b'{"memory_id": "123"}'
        >>> secret = "my-secret-token"
        >>> sig = generate_signature(payload, secret)
        >>> validate_signature(payload, sig, secret)
        True
        >>> validate_signature(payload, "sha256=invalid", secret)
        False
    """
    # Handle None or empty signature
    if not signature:
        return False

    # Signature must start with sha256=
    if not signature.startswith("sha256="):
        return False

    # Extract the hex digest from signature
    try:
        provided_digest = signature[7:]  # Remove "sha256=" prefix
    except (IndexError, TypeError):
        return False

    # Generate expected signature
    expected_digest = hmac.new(
        key=secret.encode("utf-8"),
        msg=payload, # The raw bytes are used directly
        digestmod=hashlib.sha256,
    ).hexdigest()


    # Use timing-safe comparison to prevent timing attacks
    try:
        return hmac.compare_digest(provided_digest, expected_digest)
    except (TypeError, ValueError):
        return False


def sign_request(payload: Union[bytes, str], secret: str) -> dict[str, str]:
    """
    Generate headers for a signed webhook request.

    Args:
        payload: The request body (bytes or string)
        secret: The shared secret token

    Returns:
        Dictionary with Content-Type and X-Webhook-Signature headers

    Example:
        >>> headers = sign_request('{"data": "test"}', "secret")
        >>> "X-Webhook-Signature" in headers
        True
    """
    if isinstance(payload, str):
        payload = payload.encode("utf-8")

    signature = generate_signature(payload, secret)

    return {
        "Content-Type": "application/json",
        "X-Webhook-Signature": signature,
    }


async def verify_memevolve_signature(request: Request) -> bool:
    """
    FastAPI dependency to verify HMAC-SHA256 signature for MemEvolve webhooks.
    
    Usage:
        @router.post("/endpoint", dependencies=[Depends(verify_memevolve_signature)])
        async def handler():
            ...
    
    Args:
        request: FastAPI Request object
        
    Returns:
        True if signature is valid
        
    Raises:
        HTTPException: 400 if header missing, 401 if invalid, 500 if secret not configured
        
    Feature: 009-memevolve-integration
    """
    signature_header = request.headers.get("X-Webhook-Signature")
    if not signature_header:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="X-Webhook-Signature header missing"
        )
    
    body = await request.body()
    secret = (
        os.getenv("MEMEVOLVE_HMAC_SECRET")
        or os.getenv("DIONYSUS_HMAC_SECRET")
        or ""
    )
    
    if not secret:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail="MEMEVOLVE_HMAC_SECRET or DIONYSUS_HMAC_SECRET not configured"
        )
    
    if not validate_signature(body, signature_header, secret):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="Invalid signature"
        )
    
    return True
