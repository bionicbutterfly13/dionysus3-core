"""
VPS Gateway Enforcement
Feature: 069-vps-gateway-enforcement

Centralizes outbound VPS communication and restricts it to approved hosts.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from typing import Any, Optional
from urllib.parse import urlparse

import httpx

from api.services.hmac_utils import sign_request


_DEFAULT_ALLOWED_HOSTS = {"n8n", "72.61.78.89", "localhost", "127.0.0.1"}


def _load_allowed_hosts() -> set[str]:
    raw = os.getenv("VPS_GATEWAY_ALLOWED_HOSTS", "").strip()
    if raw:
        return {host.strip().lower() for host in raw.split(",") if host.strip()}
    return {host.lower() for host in _DEFAULT_ALLOWED_HOSTS}


@dataclass(frozen=True)
class VpsGatewayConfig:
    """Configuration for VPS gateway enforcement."""

    allowed_hosts: set[str] = field(default_factory=_load_allowed_hosts)
    hmac_secret: str = ""
    default_timeout_seconds: float = 30.0


class VpsGatewayClient:
    """
    Enforces outbound requests to approved VPS gateway hosts.
    """

    def __init__(self, config: Optional[VpsGatewayConfig] = None):
        self.config = config or VpsGatewayConfig()
        self._allowed_hosts = {host.lower() for host in self.config.allowed_hosts}
        if not self._allowed_hosts:
            raise ValueError("VPS gateway allowed_hosts must not be empty")

    def _validate_url(self, url: str) -> None:
        parsed = urlparse(url)
        if parsed.scheme not in {"http", "https"}:
            raise ValueError(f"Unsupported URL scheme for VPS gateway: {parsed.scheme}")
        host = (parsed.hostname or "").lower()
        if not host or host not in self._allowed_hosts:
            raise ValueError(f"VPS gateway blocked host: {host or 'unknown'}")

    def _build_headers(
        self, payload_bytes: bytes, headers: Optional[dict[str, str]]
    ) -> dict[str, str]:
        request_headers = {"Content-Type": "application/json"}
        if headers:
            request_headers.update(headers)

        if self.config.hmac_secret and "X-Webhook-Signature" not in request_headers:
            request_headers.update(sign_request(payload_bytes, self.config.hmac_secret))

        return request_headers

    async def post_json(
        self,
        url: str,
        payload: Any,
        timeout: Optional[float] = None,
        headers: Optional[dict[str, str]] = None,
    ) -> dict[str, Any]:
        self._validate_url(url)

        if isinstance(payload, (bytes, bytearray)):
            payload_bytes = bytes(payload)
        elif isinstance(payload, str):
            payload_bytes = payload.encode("utf-8")
        else:
            payload_bytes = json.dumps(payload, default=str).encode("utf-8")

        request_headers = self._build_headers(payload_bytes, headers)
        request_timeout = timeout or self.config.default_timeout_seconds

        async with httpx.AsyncClient(timeout=request_timeout) as client:
            response = await client.post(
                url,
                content=payload_bytes,
                headers=request_headers,
            )

        if response.status_code == 200:
            return response.json() if response.text else {"success": True}

        return {
            "success": False,
            "status_code": response.status_code,
            "error": f"Webhook returned {response.status_code}: {response.text}",
        }

    async def get_status(
        self,
        url: str,
        timeout: Optional[float] = None,
        headers: Optional[dict[str, str]] = None,
    ) -> int:
        self._validate_url(url)
        request_timeout = timeout or self.config.default_timeout_seconds

        async with httpx.AsyncClient(timeout=request_timeout) as client:
            response = await client.get(url, headers=headers)

        return response.status_code
