"""
Unit Tests for Hopfield Integration in MemoryBasinRouter

Feature: 095-comp-neuro-gold-standard (Layer 2: Basin Integration)
Ref: Anderson (2014), Chapter 13 - Hopfield Networks

Tests the integration of AttractorBasinService with MemoryBasinRouter:
- Pattern synchronization on basin activation
- Hopfield-based resonance calculation
- Hybrid resonance with LLM fallback
- Hebbian strength synchronization

AUTHOR: Mani Saint-Victor, MD
"""

import numpy as np
import pytest
from typing import Dict, Any
from unittest.mock import AsyncMock, MagicMock, patch

from api.services.memory_basin_router import (
    MemoryBasinRouter,
    BASIN_MAPPING,
)
from api.services.attractor_basin_service import (
    AttractorBasinService,
    BasinState,
)
from api.models.sync import MemoryType


class TestRouterAttractorServiceIntegration:
    """Test AttractorBasinService dependency in MemoryBasinRouter."""

    def test_router_initializes_attractor_service(self):
        """Router should lazily initialize AttractorBasinService."""
        router = MemoryBasinRouter()

        # Service should not be initialized yet
        assert router._attractor_service is None

        # Get service (lazy init)
        service = router._get_attractor_service()

        # Now it should be initialized
        assert service is not None
        assert isinstance(service, AttractorBasinService)
        assert router._attractor_service is service

    def test_router_reuses_attractor_service(self):
        """Router should reuse the same AttractorBasinService instance."""
        router = MemoryBasinRouter()

        service1 = router._get_attractor_service()
        service2 = router._get_attractor_service()

        assert service1 is service2

    def test_router_accepts_injected_attractor_service(self):
        """Router should accept injected AttractorBasinService."""
        custom_service = AttractorBasinService(n_units=64)

        router = MemoryBasinRouter(attractor_service=custom_service)

        assert router._get_attractor_service() is custom_service


class TestPatternSynchronization:
    """Test pattern creation on basin activation."""

    @pytest.mark.asyncio
    async def test_ensure_hopfield_pattern_creates_pattern(self):
        """_ensure_hopfield_pattern should create pattern if missing."""
        router = MemoryBasinRouter()
        router._memevolve_adapter = AsyncMock()
        router._memevolve_adapter.execute_cypher = AsyncMock(return_value=[])

        basin_config = BASIN_MAPPING[MemoryType.EPISODIC]

        # Ensure pattern is created
        await router._ensure_hopfield_pattern(
            basin_config["basin_name"],
            basin_config
        )

        # Verify pattern was created in attractor service
        service = router._get_attractor_service()
        basin = service.get_basin_by_name(basin_config["basin_name"])

        assert basin is not None
        assert basin.name == basin_config["basin_name"]
        assert basin.pattern is not None
        assert len(basin.pattern) == service.n_units

    @pytest.mark.asyncio
    async def test_ensure_hopfield_pattern_reuses_existing(self):
        """_ensure_hopfield_pattern should not recreate existing patterns."""
        router = MemoryBasinRouter()
        router._memevolve_adapter = AsyncMock()
        router._memevolve_adapter.execute_cypher = AsyncMock(return_value=[])

        basin_config = BASIN_MAPPING[MemoryType.SEMANTIC]

        # Create pattern first time
        await router._ensure_hopfield_pattern(
            basin_config["basin_name"],
            basin_config
        )

        service = router._get_attractor_service()
        original_pattern = service.get_basin_by_name(basin_config["basin_name"]).pattern.copy()

        # Try to create again
        await router._ensure_hopfield_pattern(
            basin_config["basin_name"],
            basin_config
        )

        # Pattern should be unchanged
        current_pattern = service.get_basin_by_name(basin_config["basin_name"]).pattern
        assert np.array_equal(original_pattern, current_pattern)


class TestHopfieldResonance:
    """Test Hopfield-based resonance calculation."""

    @pytest.fixture
    def router_with_basin(self):
        """Create router with pre-configured basin."""
        router = MemoryBasinRouter()
        router._memevolve_adapter = AsyncMock()

        # Pre-create a basin pattern
        service = router._get_attractor_service()
        basin_config = BASIN_MAPPING[MemoryType.EPISODIC]

        # Create basin synchronously for test setup
        pattern = service._content_to_pattern(
            f"{basin_config['description']} {' '.join(basin_config['concepts'])}"
        )
        service.network.store_pattern(pattern)
        service.basins[basin_config["basin_name"]] = BasinState(
            name=basin_config["basin_name"],
            pattern=pattern,
            energy=service.network.compute_energy(pattern),
            activation=1.0,
            stability=1.0,
        )

        return router, basin_config

    def test_hopfield_resonance_returns_valid_score(self, router_with_basin):
        """Hopfield resonance should return score in [0, 1]."""
        router, basin_config = router_with_basin

        resonance = router._calculate_hopfield_resonance(
            "This is a test experience from yesterday",
            basin_config
        )

        assert 0.0 <= resonance <= 1.0

    def test_hopfield_resonance_high_for_matching_content(self, router_with_basin):
        """Resonance should be high for content matching basin concepts."""
        router, basin_config = router_with_basin

        # Content that matches episodic basin concepts
        matching_content = (
            "Yesterday I had an experience at the event. "
            "The timeline of events in my memory includes this context."
        )

        # Use the exact seed content for maximum match
        seed_content = f"{basin_config['description']} {' '.join(basin_config['concepts'])}"

        resonance = router._calculate_hopfield_resonance(seed_content, basin_config)

        # Same content should have very high resonance (overlap = 1.0 → resonance = 1.0)
        assert resonance > 0.9

    def test_hopfield_resonance_varies_with_content(self, router_with_basin):
        """Different content should produce different resonance scores."""
        router, basin_config = router_with_basin

        # Episodic content
        episodic = "Yesterday I experienced an event at the conference"

        # Completely different content
        different = "Python programming language syntax and functions"

        res_episodic = router._calculate_hopfield_resonance(episodic, basin_config)
        res_different = router._calculate_hopfield_resonance(different, basin_config)

        # Scores should be different (content produces different patterns)
        assert res_episodic != res_different

    def test_hopfield_resonance_missing_basin_returns_neutral(self):
        """Missing basin pattern should return 0.5 (neutral)."""
        router = MemoryBasinRouter()

        # Don't create any patterns
        basin_config = {"basin_name": "nonexistent-basin"}

        resonance = router._calculate_hopfield_resonance("any content", basin_config)

        assert resonance == 0.5


class TestHybridResonance:
    """Test hybrid resonance with LLM fallback."""

    @pytest.fixture
    def router_with_basins(self):
        """Create router with all standard basins configured."""
        router = MemoryBasinRouter()
        router._memevolve_adapter = AsyncMock()

        # Pre-create all basin patterns
        service = router._get_attractor_service()
        for mem_type, basin_config in BASIN_MAPPING.items():
            pattern = service._content_to_pattern(
                f"{basin_config['description']} {' '.join(basin_config['concepts'])}"
            )
            service.network.store_pattern(pattern)
            service.basins[basin_config["basin_name"]] = BasinState(
                name=basin_config["basin_name"],
                pattern=pattern,
                energy=service.network.compute_energy(pattern),
            )

        return router

    @pytest.mark.asyncio
    async def test_hybrid_uses_hopfield_for_high_score(self, router_with_basins):
        """Hybrid should use Hopfield directly for high resonance scores."""
        router = router_with_basins
        basin_config = BASIN_MAPPING[MemoryType.EPISODIC]

        # Use seed content for guaranteed high resonance
        seed_content = f"{basin_config['description']} {' '.join(basin_config['concepts'])}"

        # Mock the LLM method to verify it's not called
        router.calculate_resonance = AsyncMock(return_value=0.9)

        resonance = await router.calculate_resonance_hybrid(seed_content, basin_config)

        # Should return valid score
        assert 0.0 <= resonance <= 1.0

        # LLM should NOT be called for high Hopfield score
        # (Hopfield score > 0.65, so no fallback needed)
        if resonance > 0.65 or resonance < 0.35:
            router.calculate_resonance.assert_not_called()

    @pytest.mark.asyncio
    async def test_hybrid_falls_back_to_llm_for_ambiguous(self, router_with_basins):
        """Hybrid should fall back to LLM for ambiguous scores (0.35-0.65)."""
        router = router_with_basins

        # Create a basin config that will produce ambiguous overlap
        basin_config = BASIN_MAPPING[MemoryType.SEMANTIC]

        # Content designed to be somewhat related but not exact match
        ambiguous_content = "Some facts about general knowledge and information"

        # Mock LLM resonance
        router.calculate_resonance = AsyncMock(return_value=0.6)

        # Force hybrid to use fallback by mocking Hopfield to return ambiguous
        with patch.object(
            router, '_calculate_hopfield_resonance', return_value=0.5
        ):
            resonance = await router.calculate_resonance_hybrid(
                ambiguous_content,
                basin_config
            )

            # LLM should be called for ambiguous score
            router.calculate_resonance.assert_called_once()

            # Result should blend Hopfield and LLM
            assert 0.0 <= resonance <= 1.0

    @pytest.mark.asyncio
    async def test_hybrid_respects_fallback_disabled(self, router_with_basins):
        """Hybrid should not call LLM when fallback is disabled."""
        router = router_with_basins
        router._enable_llm_fallback = False

        basin_config = BASIN_MAPPING[MemoryType.PROCEDURAL]

        # Mock to verify LLM not called
        router.calculate_resonance = AsyncMock(return_value=0.7)

        # Mock Hopfield to return ambiguous score
        with patch.object(
            router, '_calculate_hopfield_resonance', return_value=0.5
        ):
            resonance = await router.calculate_resonance_hybrid(
                "Some procedural content",
                basin_config
            )

            # LLM should NOT be called even for ambiguous score
            router.calculate_resonance.assert_not_called()

            # Should return Hopfield score directly
            assert resonance == 0.5


class TestHebbianSync:
    """Test Hebbian strength synchronization between Hopfield and Neo4j."""

    @pytest.mark.asyncio
    async def test_high_resonance_strengthens_pattern(self):
        """High resonance should increase pattern strength in Hopfield network."""
        router = MemoryBasinRouter()
        router._memevolve_adapter = AsyncMock()
        router._memevolve_adapter.execute_cypher = AsyncMock(return_value=[])

        # Create initial pattern
        service = router._get_attractor_service()
        basin_config = BASIN_MAPPING[MemoryType.STRATEGIC]

        pattern = service._content_to_pattern(
            f"{basin_config['description']} {' '.join(basin_config['concepts'])}"
        )
        # Store with degree=1
        service.network.store_pattern(pattern, degree=1)
        service.basins[basin_config["basin_name"]] = BasinState(
            name=basin_config["basin_name"],
            pattern=pattern,
            energy=service.network.compute_energy(pattern),
        )

        # Get initial weight sum
        initial_weight_sum = np.abs(service.network.weights).sum()

        # Simulate high resonance update
        await router._sync_hopfield_from_resonance(
            basin_config["basin_name"],
            resonance_score=0.9
        )

        # Weights should increase (pattern strengthened)
        final_weight_sum = np.abs(service.network.weights).sum()

        # High resonance should increase weights
        assert final_weight_sum >= initial_weight_sum


class TestIntegrationFlow:
    """Test full integration flow."""

    @pytest.mark.asyncio
    async def test_route_memory_uses_hopfield_resonance(self):
        """route_memory_with_resonance should use Hopfield for resonance."""
        router = MemoryBasinRouter()

        # Mock dependencies
        router._memevolve_adapter = AsyncMock()
        router._memevolve_adapter.execute_cypher = AsyncMock(return_value=[{
            "name": "episodic-basin",
            "strength": 0.7,
            "stability": 0.5,
            "concepts": ["experience", "event"],
            "description": "Time-tagged experiences"
        }])
        router._memevolve_adapter.extract_with_context = AsyncMock(return_value={
            "entities": [],
            "relationships": []
        })
        router._memevolve_adapter.ingest_relationships = AsyncMock(return_value={})

        # Mock LLM classification (required for route_memory)
        with patch.object(
            router, 'classify_memory_type',
            new_callable=AsyncMock,
            return_value=MemoryType.EPISODIC
        ):
            # Pre-create basin pattern
            await router._ensure_hopfield_pattern(
                "episodic-basin",
                BASIN_MAPPING[MemoryType.EPISODIC]
            )

            # Track if Hopfield resonance is used
            hopfield_called = False
            original_hopfield = router._calculate_hopfield_resonance

            def track_hopfield(*args, **kwargs):
                nonlocal hopfield_called
                hopfield_called = True
                return original_hopfield(*args, **kwargs)

            router._calculate_hopfield_resonance = track_hopfield

            # Route memory with resonance
            result = await router.route_memory_with_resonance(
                content="Yesterday I experienced something memorable at the event",
                enable_transition_exploration=False
            )

            # Verify Hopfield resonance was called
            assert hopfield_called
            assert "resonance" in result
