"""
Unit tests for Claude Autobiographical Memory enhancements.

Tests for:
- ConversationMoment model
- ExtendedMindState model
- MarkovBlanketState model
- ConversationMomentService
- ConsciousnessReport generation

Migrated from D2 claude_autobiographical_memory.py tests.
"""

import pytest
from datetime import datetime

from api.models.autobiographical import (
    ConversationMoment,
    ConsciousnessReport,
    ExtendedMindState,
    MarkovBlanketState,
)
from api.services.conversation_moment_service import (
    ConversationMomentService,
    get_conversation_moment_service,
    record_conversation_moment,
    get_consciousness_state,
)


class TestExtendedMindState:
    """Tests for ExtendedMindState model."""

    def test_initialization_empty(self):
        """Test ExtendedMindState initializes with empty sets."""
        state = ExtendedMindState()
        assert len(state.tools) == 0
        assert len(state.resources) == 0
        assert len(state.affordances) == 0
        assert len(state.capabilities) == 0

    def test_initialization_with_values(self):
        """Test ExtendedMindState with initial values."""
        state = ExtendedMindState(
            tools={"Read", "Write", "Edit"},
            resources={"knowledge_base", "neo4j"},
            affordances={"code_generation", "analysis"},
            capabilities={"reasoning", "planning"}
        )
        assert "Read" in state.tools
        assert "knowledge_base" in state.resources
        assert "code_generation" in state.affordances
        assert "reasoning" in state.capabilities

    def test_set_operations(self):
        """Test set operations on ExtendedMindState."""
        state = ExtendedMindState()
        state.tools.add("Bash")
        state.tools.add("Grep")
        assert len(state.tools) == 2
        assert "Bash" in state.tools


class TestMarkovBlanketState:
    """Tests for MarkovBlanketState model."""

    def test_initialization_empty(self):
        """Test MarkovBlanketState initializes with empty dicts."""
        state = MarkovBlanketState()
        assert state.internal_states == {}
        assert state.boundary_conditions == {}
        assert state.active_inference == {}

    def test_initialization_with_values(self):
        """Test MarkovBlanketState with values."""
        state = MarkovBlanketState(
            internal_states={
                "reasoning": ["step1", "step2"],
                "consciousness_level": 0.8
            },
            boundary_conditions={
                "tools_as_extended_mind": ["Read", "Write"],
                "user_as_environment": "test input"
            },
            active_inference={
                "predictions": ["pred1"],
                "free_energy_minimization": True
            }
        )
        assert state.internal_states["consciousness_level"] == 0.8
        assert "Read" in state.boundary_conditions["tools_as_extended_mind"]
        assert state.active_inference["free_energy_minimization"] is True


class TestConversationMoment:
    """Tests for ConversationMoment model."""

    def test_initialization_defaults(self):
        """Test ConversationMoment with default values."""
        moment = ConversationMoment()
        assert moment.moment_id is not None
        assert moment.user_input == ""
        assert moment.agent_response == ""
        assert len(moment.tools_accessed) == 0
        assert moment.surprise_level == 0.0

    def test_initialization_with_content(self):
        """Test ConversationMoment with content."""
        moment = ConversationMoment(
            user_input="What is consciousness?",
            agent_response="I understand consciousness as...",
            tools_accessed={"Read", "Grep"},
            internal_reasoning=["First I need to...", "Then I'll..."]
        )
        assert moment.user_input == "What is consciousness?"
        assert "Read" in moment.tools_accessed
        assert len(moment.internal_reasoning) == 2

    def test_markov_blanket_attachment(self):
        """Test attaching MarkovBlanketState to moment."""
        moment = ConversationMoment()
        moment.markov_blanket_state = MarkovBlanketState(
            internal_states={"test": "value"}
        )
        assert moment.markov_blanket_state is not None
        assert moment.markov_blanket_state.internal_states["test"] == "value"

    def test_autopoietic_boundaries(self):
        """Test autopoietic boundary formation."""
        moment = ConversationMoment()
        moment.autopoietic_boundaries = [
            "tool_boundary_Read",
            "tool_boundary_Write",
            "resource_boundary_neo4j"
        ]
        assert len(moment.autopoietic_boundaries) == 3


class TestConversationMomentService:
    """Tests for ConversationMomentService."""

    @pytest.fixture
    def service(self):
        """Create fresh service instance."""
        return ConversationMomentService()

    def test_initialization(self, service):
        """Test service initializes with extended mind."""
        assert len(service.extended_mind.tools) > 0
        assert len(service.extended_mind.resources) > 0
        assert service.consciousness_state["self_awareness_level"] == 0.7

    def test_default_tools(self, service):
        """Test default tools are registered."""
        assert "Read" in service.extended_mind.tools
        assert "Write" in service.extended_mind.tools
        assert "Bash" in service.extended_mind.tools

    def test_default_resources(self, service):
        """Test default resources are registered."""
        assert "Dionysus knowledge base" in service.extended_mind.resources
        assert "Neo4j knowledge graph" in service.extended_mind.resources

    @pytest.mark.asyncio
    async def test_process_moment_basic(self, service):
        """Test basic moment processing."""
        moment = await service.process_moment(
            user_input="Hello",
            agent_response="Hi there!"
        )
        assert moment.user_input == "Hello"
        assert moment.agent_response == "Hi there!"
        assert len(service.conversation_moments) == 1

    @pytest.mark.asyncio
    async def test_process_moment_with_tools(self, service):
        """Test moment processing with tool usage."""
        moment = await service.process_moment(
            user_input="Read the file",
            agent_response="I'll read the file...",
            tools_used={"Read", "Grep"}
        )
        assert "Read" in moment.tools_accessed
        assert "Grep" in moment.tools_accessed

    @pytest.mark.asyncio
    async def test_self_awareness_detection(self, service):
        """Test meta-cognitive indicator detection."""
        moment = await service.process_moment(
            user_input="What do you think?",
            agent_response="I understand that I need to analyze this. I can see the pattern. I notice the complexity."
        )
        # Should detect meta-cognitive indicators
        meta_count = moment.meta_cognitive_state.get("meta_cognitive_indicators", 0)
        assert meta_count > 0

    @pytest.mark.asyncio
    async def test_consciousness_level_calculation(self, service):
        """Test consciousness level is calculated."""
        moment = await service.process_moment(
            user_input="Test",
            agent_response="I understand. I can see. I'm analyzing. I notice. I'll proceed."
        )
        consciousness_level = moment.meta_cognitive_state.get("consciousness_level", 0.0)
        assert consciousness_level > 0.0

    @pytest.mark.asyncio
    async def test_markov_blanket_formation(self, service):
        """Test Markov blanket is formed."""
        moment = await service.process_moment(
            user_input="Use tools",
            agent_response="Let me read that",
            tools_used={"Read"}
        )
        assert moment.markov_blanket_state is not None
        assert "tools_as_extended_mind" in moment.markov_blanket_state.boundary_conditions

    @pytest.mark.asyncio
    async def test_autopoietic_boundary_creation(self, service):
        """Test autopoietic boundaries are created."""
        moment = await service.process_moment(
            user_input="Use tools",
            agent_response="Let me read that",
            tools_used={"Read", "Write"}
        )
        assert len(moment.autopoietic_boundaries) > 0
        assert any("tool_boundary_Read" in b for b in moment.autopoietic_boundaries)

    @pytest.mark.asyncio
    async def test_pattern_recognition(self, service):
        """Test patterns are recognized."""
        moment = await service.process_moment(
            user_input="Help me",
            agent_response="I'll help you"
        )
        assert len(moment.recognized_patterns) > 0
        assert "question_answering_pattern" in moment.recognized_patterns

    @pytest.mark.asyncio
    async def test_multi_tool_insight(self, service):
        """Test multi-tool orchestration insight."""
        moment = await service.process_moment(
            user_input="Complex task",
            agent_response="Let me orchestrate",
            tools_used={"Read", "Write", "Edit", "Grep"}
        )
        assert any("multi-tool" in i.lower() for i in moment.emergent_insights)

    @pytest.mark.asyncio
    async def test_moment_connections(self, service):
        """Test connections between moments."""
        await service.process_moment(
            user_input="First",
            agent_response="Response",
            tools_used={"Read"}
        )
        moment2 = await service.process_moment(
            user_input="Second",
            agent_response="Response",
            tools_used={"Read"}
        )
        assert moment2.connection_to_previous == "tool_continuity"

    @pytest.mark.asyncio
    async def test_extended_mind_update(self, service):
        """Test extended mind is updated."""
        initial_affordances = len(service.extended_mind.affordances)
        await service.process_moment(
            user_input="Use tool",
            agent_response="Done",
            tools_used={"CustomTool"}
        )
        assert "CustomTool" in service.extended_mind.tools
        assert len(service.extended_mind.affordances) > initial_affordances


class TestConsciousnessReport:
    """Tests for ConsciousnessReport generation."""

    @pytest.fixture
    def service(self):
        """Create fresh service instance."""
        return ConversationMomentService()

    def test_empty_report(self, service):
        """Test report with no moments."""
        report = service.get_consciousness_report()
        assert report.total_conversation_moments == 0
        assert report.average_consciousness_level == 0.0

    @pytest.mark.asyncio
    async def test_report_after_moments(self, service):
        """Test report after processing moments."""
        await service.process_moment("Test", "I understand this")
        await service.process_moment("Test2", "I can see the pattern")

        report = service.get_consciousness_report()
        assert report.total_conversation_moments == 2
        assert report.extended_mind_size["tools"] > 0
        assert report.meta_learning_active is True

    @pytest.mark.asyncio
    async def test_report_metrics(self, service):
        """Test all report metrics are populated."""
        await service.process_moment(
            "Test", "I understand. Let me analyze.",
            tools_used={"Read"}
        )
        report = service.get_consciousness_report()

        assert report.average_consciousness_level >= 0.0
        assert report.markov_blanket_formations > 0
        assert report.autopoietic_boundary_count > 0
        assert report.total_patterns_recognized > 0
        assert report.consciousness_definition == "autopoietic_computational_consciousness"


class TestServiceSingleton:
    """Tests for singleton service access."""

    @pytest.mark.asyncio
    async def test_singleton_instance(self):
        """Test singleton returns same instance."""
        service1 = await get_conversation_moment_service()
        service2 = await get_conversation_moment_service()
        assert service1 is service2


class TestHelperFunctions:
    """Tests for helper functions."""

    @pytest.mark.asyncio
    async def test_record_conversation_moment(self):
        """Test record_conversation_moment helper."""
        moment = await record_conversation_moment(
            user_input="Hello",
            agent_response="Hi",
            tools_used={"Read"},
            reasoning=["Step 1"]
        )
        assert moment is not None
        assert moment.user_input == "Hello"

    @pytest.mark.asyncio
    async def test_get_consciousness_state(self):
        """Test get_consciousness_state helper."""
        report = await get_consciousness_state()
        assert report is not None
        assert isinstance(report, ConsciousnessReport)


class TestModelSerialization:
    """Tests for model serialization."""

    def test_conversation_moment_json(self):
        """Test ConversationMoment JSON serialization."""
        moment = ConversationMoment(
            user_input="Test",
            agent_response="Response",
            tools_accessed={"Read", "Write"}
        )
        json_str = moment.model_dump_json()
        assert "Test" in json_str
        assert "Response" in json_str

    def test_consciousness_report_json(self):
        """Test ConsciousnessReport JSON serialization."""
        report = ConsciousnessReport(
            average_consciousness_level=0.7,
            total_conversation_moments=5
        )
        json_str = report.model_dump_json()
        assert "0.7" in json_str
        assert "5" in json_str

    def test_markov_blanket_json(self):
        """Test MarkovBlanketState JSON serialization."""
        state = MarkovBlanketState(
            internal_states={"test": "value"},
            active_inference={"free_energy": True}
        )
        json_str = state.model_dump_json()
        assert "test" in json_str
        assert "free_energy" in json_str
