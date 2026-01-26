import pytest
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

from api.services.graphiti_service import GraphitiConfig, GraphitiService

pytestmark = pytest.mark.asyncio


class DummyGraphiti:
    def __init__(self, **_kwargs):
        self.calls: list[bool] = []

    async def build_indices_and_constraints(self, delete_existing: bool = False) -> None:
        self.calls.append(delete_existing)


class TestGraphitiServiceInitialize:
    async def test_initialize_builds_indices(self, monkeypatch):
        from api.services import graphiti_service

        monkeypatch.setattr(graphiti_service, "_global_graphiti", None)
        monkeypatch.setattr(graphiti_service, "_get_graphiti_class", lambda: DummyGraphiti)
        monkeypatch.setenv("NEO4J_PASSWORD", "test-password")

        config = GraphitiConfig(skip_index_build=False, index_build_timeout_seconds=1)
        service = GraphitiService(config)

        await service.initialize()

        assert isinstance(graphiti_service._global_graphiti, DummyGraphiti)
        assert graphiti_service._global_graphiti.calls == [False]
        assert service._index_build_task is not None

    async def test_initialize_skips_index_build(self, monkeypatch):
        from api.services import graphiti_service

        monkeypatch.setattr(graphiti_service, "_global_graphiti", None)
        monkeypatch.setattr(graphiti_service, "_get_graphiti_class", lambda: DummyGraphiti)
        monkeypatch.setenv("NEO4J_PASSWORD", "test-password")

        config = GraphitiConfig(skip_index_build=True, index_build_timeout_seconds=1)
        service = GraphitiService(config)

        await service.initialize()

        assert isinstance(graphiti_service._global_graphiti, DummyGraphiti)
        assert graphiti_service._global_graphiti.calls == []
        assert service._index_build_task is None


class TestGraphitiServiceIngest:
    async def test_ingest_message_returns_structured_payload(self, monkeypatch):
        monkeypatch.setenv("NEO4J_PASSWORD", "test-password")
        service = GraphitiService(GraphitiConfig(group_id="test-group"))

        episode = SimpleNamespace(uuid="episode-1")
        node = SimpleNamespace(
            uuid="node-1",
            name="Node",
            labels=["Concept"],
            summary="Summary",
        )
        edge = SimpleNamespace(
            uuid="edge-1",
            name="Edge",
            fact="A->B",
            source_node_uuid="node-1",
            target_node_uuid="node-2",
        )

        mock_graphiti = MagicMock()
        mock_graphiti.add_episode = AsyncMock(
            return_value=SimpleNamespace(episode=episode, nodes=[node], edges=[edge])
        )

        monkeypatch.setattr(service, "_get_graphiti", lambda: mock_graphiti)

        result = await service.ingest_message(
            content="Hello world",
            source_description="unit-test",
            group_id="override-group",
        )

        call_kwargs = mock_graphiti.add_episode.await_args.kwargs
        assert call_kwargs["episode_body"] == "Hello world"
        assert call_kwargs["source_description"] == "unit-test"
        assert call_kwargs["group_id"] == "override-group"

        assert result["episode_uuid"] == "episode-1"
        assert result["nodes"][0]["uuid"] == "node-1"
        assert result["nodes"][0]["name"] == "Node"
        assert result["nodes"][0]["labels"] == ["Concept"]
        assert result["nodes"][0]["summary"] == "Summary"
        assert result["edges"][0]["uuid"] == "edge-1"
        assert result["edges"][0]["fact"] == "A->B"
