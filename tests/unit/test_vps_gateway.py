import importlib.util
import sys
from pathlib import Path

import pytest


def _load_audit_module():
    module_name = "api.agents.audit"
    if module_name in sys.modules:
        return sys.modules[module_name]

    module_path = Path(__file__).resolve().parents[2] / "api" / "agents" / "audit.py"
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


@pytest.mark.asyncio
async def test_gateway_rejects_unapproved_host():
    from api.services.vps_gateway import VpsGatewayClient, VpsGatewayConfig

    gateway = VpsGatewayClient(VpsGatewayConfig(allowed_hosts={"n8n.local"}))
    with pytest.raises(ValueError):
        await gateway.post_json("http://unauthorized.example/webhook", {"ok": True})


class _FakeGateway:
    def __init__(self):
        self.calls = []

    async def post_json(self, url, payload, timeout=None, headers=None):
        self.calls.append({"url": url, "payload": payload, "timeout": timeout, "headers": headers})
        return {"success": True}


@pytest.mark.asyncio
async def test_remote_sync_uses_gateway_for_webhooks():
    from api.services.remote_sync import RemoteSyncService, SyncConfig

    fake = _FakeGateway()
    service = RemoteSyncService(config=SyncConfig(webhook_url="http://n8n:5678/webhook/test"), gateway=fake)

    await service._send_to_webhook({"ping": True})

    assert fake.calls, "Expected RemoteSyncService to use the gateway for webhook calls"
    assert fake.calls[0]["url"] == service.config.webhook_url


@pytest.mark.asyncio
async def test_agent_audit_uses_gateway_for_vps_calls():
    audit_module = _load_audit_module()
    AgentAuditCallback = audit_module.AgentAuditCallback

    fake = _FakeGateway()
    audit = AgentAuditCallback(webhook_url="http://n8n:5678/webhook/agent-step", gateway=fake)

    await audit._send_payload({"ping": "audit"})

    assert fake.calls, "Expected AgentAuditCallback to use gateway for VPS calls"
    assert fake.calls[0]["url"] == audit.webhook_url
