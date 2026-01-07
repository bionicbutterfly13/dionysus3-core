"""
Unit tests for Meta-ToT Decision Service.
Feature: 041-meta-tot-engine
"""

import pytest
from unittest.mock import patch

from api.services.meta_tot_decision import (
    MetaToTDecisionConfig,
    MetaToTDecisionService,
    get_meta_tot_decision_service,
)


class TestMetaToTDecisionConfig:
    def test_defaults(self):
        config = MetaToTDecisionConfig()
        assert config.complexity_threshold == 0.7
        assert config.uncertainty_threshold == 0.6
        assert config.min_token_threshold == 160
        assert config.always_on is False

    def test_from_env_defaults(self):
        with patch.dict("os.environ", {}, clear=True):
            config = MetaToTDecisionConfig.from_env()
            assert config.complexity_threshold == 0.7
            assert config.uncertainty_threshold == 0.6
            assert config.min_token_threshold == 160
            assert config.always_on is False

    def test_from_env_custom(self):
        env = {
            "META_TOT_COMPLEXITY_THRESHOLD": "0.5",
            "META_TOT_UNCERTAINTY_THRESHOLD": "0.4",
            "META_TOT_MIN_TOKENS": "200",
            "META_TOT_ALWAYS_ON": "true",
        }
        with patch.dict("os.environ", env, clear=True):
            config = MetaToTDecisionConfig.from_env()
            assert config.complexity_threshold == 0.5
            assert config.uncertainty_threshold == 0.4
            assert config.min_token_threshold == 200
            assert config.always_on is True


class TestMetaToTDecisionService:
    def test_disabled_by_context(self):
        config = MetaToTDecisionConfig(complexity_threshold=0.0, uncertainty_threshold=0.0)
        service = MetaToTDecisionService(config)
        decision = service.decide("complex task with constraints", {"disable_meta_tot": True})
        assert decision.use_meta_tot is False
        assert decision.complexity_score == 0.0
        assert decision.uncertainty_score == 0.0
        assert "disabled by context" in decision.rationale.lower()

    def test_force_by_context(self):
        config = MetaToTDecisionConfig(complexity_threshold=1.0, uncertainty_threshold=1.0)
        service = MetaToTDecisionService(config)
        decision = service.decide("simple task", {"force_meta_tot": True})
        assert decision.use_meta_tot is True

    def test_always_on(self):
        config = MetaToTDecisionConfig(always_on=True)
        service = MetaToTDecisionService(config)
        decision = service.decide("simple", {})
        assert decision.use_meta_tot is True

    def test_complexity_threshold_triggers(self):
        config = MetaToTDecisionConfig(
            complexity_threshold=0.3,
            uncertainty_threshold=1.0,
            min_token_threshold=10,
        )
        service = MetaToTDecisionService(config)
        # Long task with constraint keywords should trigger
        long_task = "must " * 20 + "plan a strategy"
        decision = service.decide(long_task, {})
        assert decision.use_meta_tot is True
        assert decision.complexity_score >= 0.3

    def test_uncertainty_threshold_triggers(self):
        config = MetaToTDecisionConfig(
            complexity_threshold=1.0,
            uncertainty_threshold=0.3,
        )
        service = MetaToTDecisionService(config)
        decision = service.decide("simple", {"uncertainty_level": 0.5})
        assert decision.use_meta_tot is True
        assert decision.uncertainty_score >= 0.3

    def test_low_complexity_no_trigger(self):
        config = MetaToTDecisionConfig(
            complexity_threshold=0.9,
            uncertainty_threshold=0.9,
            min_token_threshold=1000,
        )
        service = MetaToTDecisionService(config)
        decision = service.decide("short", {})
        assert decision.use_meta_tot is False

    def test_thresholds_in_response(self):
        config = MetaToTDecisionConfig(complexity_threshold=0.7, uncertainty_threshold=0.6)
        service = MetaToTDecisionService(config)
        decision = service.decide("test", {})
        assert decision.thresholds["complexity_threshold"] == 0.7
        assert decision.thresholds["uncertainty_threshold"] == 0.6

    def test_complexity_scoring_constraint_terms(self):
        config = MetaToTDecisionConfig(min_token_threshold=10)
        service = MetaToTDecisionService(config)
        # Test constraint terms detection
        score_base = service._score_complexity("simple task", {})
        score_constraints = service._score_complexity("must handle constraint tradeoff risk", {})
        assert score_constraints > score_base

    def test_complexity_scoring_domain_terms(self):
        config = MetaToTDecisionConfig(min_token_threshold=10)
        service = MetaToTDecisionService(config)
        score_base = service._score_complexity("simple task", {})
        score_domain = service._score_complexity("strategy plan marketing evolution architecture", {})
        assert score_domain > score_base

    def test_uncertainty_from_context(self):
        service = MetaToTDecisionService()
        score = service._score_uncertainty("task", {"uncertainty_level": 0.8})
        assert score == 0.8

    def test_uncertainty_from_unknowns(self):
        service = MetaToTDecisionService()
        score = service._score_uncertainty("task", {"unknowns": ["a", "b", "c"]})
        assert score > 0.0

    def test_uncertainty_from_questions(self):
        service = MetaToTDecisionService()
        score_no_q = service._score_uncertainty("task", {})
        score_with_q = service._score_uncertainty("task? really? what?", {})
        assert score_with_q > score_no_q


class TestGetMetaToTDecisionService:
    def test_singleton(self):
        import api.services.meta_tot_decision as module
        module._meta_tot_decision_service = None
        svc1 = get_meta_tot_decision_service()
        svc2 = get_meta_tot_decision_service()
        assert svc1 is svc2
        module._meta_tot_decision_service = None
