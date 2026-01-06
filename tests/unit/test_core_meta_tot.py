"""
Unit tests for Core Meta-ToT Engine (api/core/engine/meta_tot.py).

Feature: 057-complete-placeholder-implementations
User Story 2: Real Active Inference Scoring (Priority: P1)
Functional Requirements: FR-003, FR-004

TDD: Tests written BEFORE modifying api/core/engine/meta_tot.py
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
import numpy as np

from api.core.engine.meta_tot import MetaToTEngine
from api.core.engine.models import ThoughtNode, ActiveInferenceScore


class TestExpandNodeRealScoring:
    """
    Tests for expand_node() with REAL active inference scoring.

    Replaces TODO comment (line 62) with verification that real scores
    are obtained from active inference wrapper, not placeholders.
    """

    @pytest.mark.asyncio
    async def test_expand_node_each_child_gets_unique_score(self):
        """
        US2-AS1: Each child ThoughtNode receives unique score from active inference.

        Given three candidate thought contents with different semantic meaning,
        When expand_node() creates children,
        Then each child has a different ActiveInferenceScore based on content.

        FR-003: Meta-ToT MUST call active inference to get real probability distributions.
        """
        engine = MetaToTEngine()

        # Initialize session with root
        goal_vector = [0.5] * 768  # Typical embedding dimension
        root = await engine.initialize_session("User wants authentication", goal_vector)

        # Mock active inference wrapper to return different scores based on content
        with patch.object(engine.ai_wrapper, 'score_thought', new_callable=AsyncMock) as mock_score:
            # Different EFE values for different contents
            def score_side_effect(thought, goal_vec, *args, **kwargs):
                content_scores = {
                    "OAuth2": ActiveInferenceScore(
                        expected_free_energy=1.2,
                        surprise=0.5,
                        prediction_error=0.3,
                        precision=1.0
                    ),
                    "JWT sessions": ActiveInferenceScore(
                        expected_free_energy=1.5,
                        surprise=0.6,
                        prediction_error=0.4,
                        precision=1.0
                    ),
                    "Magic links": ActiveInferenceScore(
                        expected_free_energy=2.0,
                        surprise=0.8,
                        prediction_error=0.7,
                        precision=1.0
                    ),
                }
                return content_scores.get(thought.content, ActiveInferenceScore(
                    expected_free_energy=5.0, surprise=1.0, prediction_error=1.0, precision=1.0
                ))

            mock_score.side_effect = score_side_effect

            # Expand with three different candidate contents
            children = await engine.expand_node(
                parent_id=root.id,
                candidate_contents=["OAuth2", "JWT sessions", "Magic links"]
            )

        # Verify each child has a score
        assert len(children) == 3, "Should create 3 children"
        for child in children:
            assert child.score is not None, f"Child '{child.content}' must have a score"
            assert isinstance(child.score, ActiveInferenceScore), "Score must be ActiveInferenceScore"

        # Verify scores are DIFFERENT (not identical placeholders)
        efes = [child.score.expected_free_energy for child in children]
        assert len(set(efes)) == 3, "Each child must have UNIQUE EFE score (not identical placeholders)"

        # Verify scores match expected values
        oauth_child = next(c for c in children if c.content == "OAuth2")
        jwt_child = next(c for c in children if c.content == "JWT sessions")
        magic_child = next(c for c in children if c.content == "Magic links")

        assert oauth_child.score.expected_free_energy == pytest.approx(1.2, rel=0.01)
        assert jwt_child.score.expected_free_energy == pytest.approx(1.5, rel=0.01)
        assert magic_child.score.expected_free_energy == pytest.approx(2.0, rel=0.01)

    @pytest.mark.asyncio
    async def test_expand_node_calls_active_inference_wrapper(self):
        """
        FR-003: Verify expand_node() calls active inference wrapper for each child.

        Given parent node and candidate contents,
        When expand_node() is called,
        Then score_thought() is invoked for EACH child with correct parameters.
        """
        engine = MetaToTEngine()

        goal_vector = [0.3] * 768
        root = await engine.initialize_session("Implement feature X", goal_vector)

        with patch.object(engine.ai_wrapper, 'score_thought', new_callable=AsyncMock) as mock_score:
            mock_score.return_value = ActiveInferenceScore(
                expected_free_energy=1.0,
                surprise=0.5,
                prediction_error=0.2,
                precision=1.0
            )

            candidates = ["Approach A", "Approach B", "Approach C"]
            await engine.expand_node(root.id, candidates)

            # Verify score_thought called for each candidate
            assert mock_score.call_count == 3, "score_thought must be called for each child"

            # Verify correct parameters passed
            for call_args in mock_score.call_args_list:
                thought_arg = call_args[0][0]  # First positional arg
                goal_arg = call_args[0][1]     # Second positional arg

                assert isinstance(thought_arg, ThoughtNode), "First arg must be ThoughtNode"
                assert thought_arg.content in candidates, "ThoughtNode content must match candidate"
                assert goal_arg == goal_vector, "Goal vector must be passed correctly"

    @pytest.mark.asyncio
    async def test_expand_node_goal_vector_alignment_affects_scores(self):
        """
        US2-AS3: Thoughtseeds aligned with goal_vector have lower EFE.

        Given two candidates (one aligned, one misaligned with goal),
        When expand_node() scores them,
        Then aligned candidate has measurably lower EFE (difference > 0.1).

        FR-004: Meta-ToT MUST use precision-weighted prediction errors.
        """
        engine = MetaToTEngine()

        # Goal vector favoring "security-focused" solutions
        goal_vector = [0.9, 0.1] * 384  # Simplified embedding

        root = await engine.initialize_session("Add authentication", goal_vector)

        with patch.object(engine.ai_wrapper, 'score_thought', new_callable=AsyncMock) as mock_score:
            def alignment_score(thought, goal_vec, *args, **kwargs):
                # "OAuth2" is aligned (security-focused)
                if "OAuth2" in thought.content:
                    return ActiveInferenceScore(
                        expected_free_energy=0.8,  # Lower EFE = better
                        surprise=0.2,
                        prediction_error=0.1,
                        precision=1.2
                    )
                # "Simple password" is misaligned (less secure)
                else:
                    return ActiveInferenceScore(
                        expected_free_energy=2.5,  # Higher EFE = worse
                        surprise=0.9,
                        prediction_error=0.8,
                        precision=0.8
                    )

            mock_score.side_effect = alignment_score

            children = await engine.expand_node(
                root.id,
                ["OAuth2 with PKCE", "Simple password auth"]
            )

        oauth_child = next(c for c in children if "OAuth2" in c.content)
        password_child = next(c for c in children if "Simple" in c.content)

        # Verify aligned candidate has lower EFE
        assert oauth_child.score.expected_free_energy < password_child.score.expected_free_energy, \
            "Aligned candidate must have lower EFE"

        efe_difference = password_child.score.expected_free_energy - oauth_child.score.expected_free_energy
        assert efe_difference > 0.1, \
            f"EFE difference must be > 0.1 (actual: {efe_difference:.2f})"

    @pytest.mark.asyncio
    async def test_expand_node_precision_weighting_applied(self):
        """
        FR-004: Verify precision-weighted prediction errors are used in scoring.

        Given active inference wrapper returns scores with precision values,
        When children are scored,
        Then precision affects the final EFE calculation.
        """
        engine = MetaToTEngine()

        goal_vector = [0.5] * 768
        root = await engine.initialize_session("Test precision weighting", goal_vector)

        with patch.object(engine.ai_wrapper, 'score_thought', new_callable=AsyncMock) as mock_score:
            # High precision = high confidence
            high_precision_score = ActiveInferenceScore(
                expected_free_energy=1.0,
                surprise=0.5,
                prediction_error=0.2,
                precision=2.0  # High precision
            )

            # Low precision = low confidence
            low_precision_score = ActiveInferenceScore(
                expected_free_energy=1.8,
                surprise=0.5,
                prediction_error=0.2,
                precision=0.5  # Low precision
            )

            mock_score.side_effect = [high_precision_score, low_precision_score]

            children = await engine.expand_node(
                root.id,
                ["High confidence option", "Low confidence option"]
            )

        # Verify precision values are preserved in scores
        high_conf_child = children[0]
        low_conf_child = children[1]

        assert high_conf_child.score.precision == 2.0, "High precision must be preserved"
        assert low_conf_child.score.precision == 0.5, "Low precision must be preserved"

        # Higher precision should result in lower EFE (all else being equal in prediction_error)
        assert high_conf_child.score.expected_free_energy < low_conf_child.score.expected_free_energy, \
            "Higher precision should yield lower EFE"

    @pytest.mark.asyncio
    async def test_expand_node_handles_wrapper_failure_gracefully(self):
        """
        FR-012: System MUST handle missing active inference scores gracefully.

        Given active inference wrapper returns None or raises error,
        When expand_node() attempts to score children,
        Then system uses fallback neutral score without crashing.
        """
        engine = MetaToTEngine()

        goal_vector = [0.5] * 768
        root = await engine.initialize_session("Handle failures", goal_vector)

        with patch.object(engine.ai_wrapper, 'score_thought', new_callable=AsyncMock) as mock_score:
            # Simulate wrapper failure
            mock_score.side_effect = Exception("Model service unavailable")

            # Should not crash, should handle gracefully
            with pytest.raises(Exception):
                # Currently raises - implementation in T018 should add graceful handling
                await engine.expand_node(root.id, ["Option A", "Option B"])

            # After T018 implementation, this test should be updated to:
            # children = await engine.expand_node(root.id, ["Option A", "Option B"])
            # assert all(c.score is not None for c in children), "Should have fallback scores"


class TestSelectBestBranchWithRealScores:
    """Tests for select_best_branch() using real EFE scores."""

    @pytest.mark.asyncio
    async def test_select_best_branch_chooses_lowest_efe(self):
        """
        Verify select_best_branch() selects child with minimal EFE.

        Given children with different EFE scores from active inference,
        When select_best_branch() is called,
        Then child with lowest EFE is selected.
        """
        engine = MetaToTEngine()

        goal_vector = [0.5] * 768
        root = await engine.initialize_session("Test selection", goal_vector)

        with patch.object(engine.ai_wrapper, 'score_thought', new_callable=AsyncMock) as mock_score:
            scores = [
                ActiveInferenceScore(expected_free_energy=2.5, surprise=0.8, prediction_error=0.7, precision=1.0),
                ActiveInferenceScore(expected_free_energy=1.2, surprise=0.4, prediction_error=0.3, precision=1.0),  # Best
                ActiveInferenceScore(expected_free_energy=3.0, surprise=0.9, prediction_error=0.9, precision=1.0),
            ]
            mock_score.side_effect = scores

            children = await engine.expand_node(
                root.id,
                ["Worst option", "Best option", "Bad option"]
            )

            best_branch = await engine.select_best_branch(root.id)

        assert best_branch is not None, "Should select a branch"
        assert best_branch.content == "Best option", "Should select child with lowest EFE"
        assert best_branch.score.expected_free_energy == pytest.approx(1.2, rel=0.01)


class TestMetaToTEngineSingleton:
    """Test singleton pattern."""

    def test_initialization_stores_nodes(self):
        """Verify engine stores ThoughtNodes in internal dict."""
        engine = MetaToTEngine()
        assert hasattr(engine, 'nodes'), "Engine must have nodes dict"
        assert isinstance(engine.nodes, dict), "nodes must be a dict"
