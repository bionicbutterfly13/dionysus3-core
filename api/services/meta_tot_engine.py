"""
Meta-ToT Engine with Active Inference Currency
Feature: 041-meta-tot-engine
"""

from __future__ import annotations

import json
import logging
import math
import random
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import uuid4

from api.models.meta_tot import MetaToTDecision, MetaToTNodeTrace, MetaToTResult, MetaToTTracePayload
from api.services.llm_service import chat_completion, GPT5_NANO
from api.services.meta_tot_trace_service import get_meta_tot_trace_service
from api.services.meta_tot_decision import get_meta_tot_decision_service
from api.services.memory_basin_router import get_memory_basin_router
from api.models.sync import MemoryType

logger = logging.getLogger("dionysus.meta_tot")


class MetaToTNodeType(str, Enum):
    ROOT = "root"
    EXPLORATION = "exploration"
    CHALLENGE = "challenge"
    EVOLUTION = "evolution"
    INTEGRATION = "integration"
    LEAF = "leaf"


class ExplorationStrategy(str, Enum):
    UCB_PREDICTION_ERROR = "ucb_prediction_error"
    THOMPSON_SAMPLING = "thompson_sampling"
    SURPRISE_MAXIMIZATION = "surprise_maximization"
    FREE_ENERGY_MINIMIZATION = "free_energy_minimization"


@dataclass
class ActiveInferenceState:
    """Active inference currency state."""

    state_id: str = field(default_factory=lambda: str(uuid4()))
    timestamp: datetime = field(default_factory=datetime.utcnow)
    prediction_error: float = 0.0
    free_energy: float = 0.0
    surprise: float = 0.0
    precision: float = 1.0
    beliefs: Dict[str, float] = field(default_factory=dict)
    prediction_updates: Dict[str, float] = field(default_factory=dict)
    reasoning_level: int = 0
    parent_state_id: Optional[str] = None

    def compute_prediction_error(self, observation: Dict[str, float]) -> float:
        total_error = 0.0
        for key, observed_value in observation.items():
            predicted_value = self.beliefs.get(key, observed_value)
            error = abs(observed_value - predicted_value)
            total_error += error * self.precision
        self.prediction_error = total_error
        return total_error

    def update_beliefs(self, prediction_error: float, learning_rate: float = 0.1) -> None:
        for belief_key, belief_value in list(self.beliefs.items()):
            gradient = self.prediction_updates.get(belief_key, 0.0)
            belief_update = -learning_rate * gradient * prediction_error
            self.beliefs[belief_key] = max(0.0, min(1.0, belief_value + belief_update))
        self.free_energy = prediction_error + 0.01 * len(self.beliefs)
        self.surprise = -math.log(max(0.001, 1.0 - min(prediction_error, 0.99)))


@dataclass
class MetaToTNode:
    node_id: str = field(default_factory=lambda: str(uuid4()))
    node_type: MetaToTNodeType = MetaToTNodeType.ROOT
    depth: int = 0
    parent_id: Optional[str] = None
    children_ids: List[str] = field(default_factory=list)
    thought_content: str = ""
    cpa_domain: str = "explore"
    active_inference_state: ActiveInferenceState = field(default_factory=ActiveInferenceState)
    visit_count: int = 0
    value_estimate: float = 0.0
    uncertainty_estimate: float = 1.0
    score: float = 0.0

    def compute_ucb_score(self, total_parent_visits: int, exploration_constant: float = 2.0) -> float:
        if self.visit_count == 0:
            return float("inf")
        exploitation = self.value_estimate
        exploration = exploration_constant * math.sqrt(
            math.log(max(total_parent_visits, 1)) / self.visit_count
        )
        prediction_bonus = 1.0 / (1.0 + self.active_inference_state.prediction_error)
        return exploitation + exploration + prediction_bonus

    def update_from_rollout(self, reward: float, prediction_error: float, learning_rate: float = 0.1) -> None:
        self.visit_count += 1
        prediction_weight = 1.0 / (1.0 + prediction_error)
        weighted_reward = reward * prediction_weight
        self.value_estimate += learning_rate * (weighted_reward - self.value_estimate)
        self.uncertainty_estimate = 1.0 / math.sqrt(self.visit_count + 1)
        self.active_inference_state.update_beliefs(prediction_error, learning_rate)
        self.score = self.value_estimate


@dataclass
class MetaToTConfig:
    max_depth: int = 4
    simulation_count: int = 32
    exploration_constant: float = 2.0
    branching_factor: int = 3
    time_budget_seconds: float = 5.0
    use_llm: bool = True
    llm_model: str = GPT5_NANO
    persist_trace: bool = True
    random_seed: Optional[int] = None

    @classmethod
    def from_overrides(cls, overrides: Optional[Dict[str, Any]] = None) -> "MetaToTConfig":
        if not overrides:
            return cls()
        base = cls()
        for key, value in overrides.items():
            if hasattr(base, key):
                setattr(base, key, value)
        return base


class POMCPActiveInferencePlanner:
    """Simplified POMCP planner with active inference scoring."""

    def __init__(self, max_depth: int = 8, simulation_count: int = 50, exploration_constant: float = 2.0):
        self.max_depth = max_depth
        self.simulation_count = simulation_count
        self.exploration_constant = exploration_constant
        self.observation_history: List[Dict[str, Any]] = []
        self.belief_state: ActiveInferenceState = ActiveInferenceState()

    async def plan(self, observation: Dict[str, float], actions: List[str]) -> tuple[str, float]:
        if not actions:
            return "", 0.0

        prediction_error = self.belief_state.compute_prediction_error(observation)
        self.belief_state.update_beliefs(prediction_error)
        self.observation_history.append(observation)

        best_action = actions[0]
        best_value = float("-inf")

        for idx in range(self.simulation_count):
            action = actions[idx % len(actions)]
            reward = 1.0 / (1.0 + prediction_error)
            noise = random.random() * 0.05
            value = reward + noise
            if value > best_value:
                best_value = value
                best_action = action

        return best_action, best_value


class MetaToTEngine:
    """Meta-ToT engine with active inference currency and CPA domain expansion."""

    def __init__(self, config: Optional[MetaToTConfig] = None):
        self.config = config or MetaToTConfig()
        self.node_storage: Dict[str, MetaToTNode] = {}
        self.reasoning_sessions: Dict[str, Dict[str, Any]] = {}
        self.cpa_strategies = {
            "explore": ExplorationStrategy.SURPRISE_MAXIMIZATION,
            "challenge": ExplorationStrategy.UCB_PREDICTION_ERROR,
            "evolve": ExplorationStrategy.THOMPSON_SAMPLING,
            "integrate": ExplorationStrategy.FREE_ENERGY_MINIMIZATION,
        }

    async def run(
        self,
        problem: str,
        context: Dict[str, Any],
        config_overrides: Optional[Dict[str, Any]] = None,
        decision: Optional[MetaToTDecision] = None,
    ) -> tuple[MetaToTResult, Optional[MetaToTTracePayload]]:
        config = MetaToTConfig.from_overrides({**self.config.__dict__, **(config_overrides or {})})
        if config.random_seed is not None:
            random.seed(config.random_seed)

        session_id = str(uuid4())
        start_time = time.time()

        initial_observation = self._build_observation(problem, context)
        initial_state = ActiveInferenceState()
        initial_error = initial_state.compute_prediction_error(initial_observation)
        initial_state.update_beliefs(initial_error)

        root_node = MetaToTNode(
            node_type=MetaToTNodeType.ROOT,
            active_inference_state=initial_state,
            thought_content=problem,
            cpa_domain="explore",
        )
        self.node_storage[root_node.node_id] = root_node

        expansion_result = await self._expand_tree(root_node, context, config)
        actions = self._generate_actions(root_node)
        pomcp_planner = POMCPActiveInferencePlanner(
            max_depth=config.max_depth,
            simulation_count=config.simulation_count,
            exploration_constant=config.exploration_constant,
        )
        best_action, action_value = await pomcp_planner.plan(initial_observation, actions)
        best_path = self._select_best_path(root_node)

        confidence = max(0.0, min(1.0, action_value))
        metrics = {
            "total_prediction_error": expansion_result["total_prediction_error"],
            "total_free_energy": expansion_result["total_free_energy"],
            "processing_time": time.time() - start_time,
            "branch_count": expansion_result["branch_count"],
            "time_budget_seconds": config.time_budget_seconds,
        }

        trace_payload = MetaToTTracePayload(
            trace_id=str(uuid4()),
            session_id=session_id,
            decision=decision,
            best_path=best_path,
            selected_action=best_action,
            confidence=confidence,
            metrics=metrics,
            nodes=[self._node_to_trace(node) for node in self.node_storage.values()],
        )

        trace_id = None
        if config.persist_trace:
            trace_service = get_meta_tot_trace_service()
            trace_id = await trace_service.store_trace(trace_payload)

        await self._update_basins(problem, context, best_path)

        result = MetaToTResult(
            session_id=session_id,
            best_path=best_path,
            confidence=confidence,
            metrics=metrics,
            decision=decision,
            trace_id=trace_id,
        )

        if decision is not None:
            decision_service = get_meta_tot_decision_service()
            await decision_service.update_from_result(decision, result)

        self.reasoning_sessions[session_id] = {
            "decision": decision,
            "result": result.model_dump(),
            "trace": trace_payload.model_dump(),
        }

        return result, trace_payload

    def _build_observation(self, problem: str, context: Dict[str, Any]) -> Dict[str, float]:
        context_size = len(json.dumps(context)) if context else 0
        constraints = context.get("constraints", []) if isinstance(context.get("constraints", []), list) else []
        return {
            "problem_complexity": min(len(problem) / 1000.0, 1.0),
            "context_richness": min(context_size / 2000.0, 1.0),
            "constraint_density": min(len(constraints) / 10.0, 1.0),
        }

    async def _expand_tree(
        self,
        root_node: MetaToTNode,
        context: Dict[str, Any],
        config: MetaToTConfig,
    ) -> Dict[str, Any]:
        cpa_domains = ["explore", "challenge", "evolve", "integrate"]
        current_nodes = [root_node]
        total_prediction_error = 0.0
        total_free_energy = 0.0
        branch_count = 0

        for depth in range(config.max_depth):
            domain = cpa_domains[depth % len(cpa_domains)]
            next_nodes: List[MetaToTNode] = []

            for node in current_nodes:
                candidates = await self._generate_candidates(node, domain, context, config)
                for candidate in candidates[: config.branching_factor]:
                    child_state = self._inherit_state(node)
                    child_node = MetaToTNode(
                        node_type=self._domain_to_node_type(domain),
                        depth=node.depth + 1,
                        parent_id=node.node_id,
                        thought_content=candidate,
                        cpa_domain=domain,
                        active_inference_state=child_state,
                    )
                    node.children_ids.append(child_node.node_id)
                    self.node_storage[child_node.node_id] = child_node
                    branch_count += 1

                    observation = self._build_observation(candidate, context)
                    error = child_node.active_inference_state.compute_prediction_error(observation)
                    child_node.active_inference_state.update_beliefs(error)
                    child_node.score = 1.0 / (1.0 + child_node.active_inference_state.free_energy)
                    total_prediction_error += error
                    total_free_energy += child_node.active_inference_state.free_energy
                    next_nodes.append(child_node)

            current_nodes = next_nodes or current_nodes

        await self._run_mcts(root_node, config)

        return {
            "total_prediction_error": total_prediction_error,
            "total_free_energy": total_free_energy,
            "branch_count": branch_count,
        }

    async def _run_mcts(self, root_node: MetaToTNode, config: MetaToTConfig) -> None:
        start_time = time.time()
        for _ in range(config.simulation_count):
            if time.time() - start_time > config.time_budget_seconds:
                break
            path = self._select_path(root_node, config.exploration_constant)
            leaf = path[-1]
            reward = self._evaluate_leaf(leaf)
            prediction_error = leaf.active_inference_state.prediction_error
            for node in path:
                node.update_from_rollout(reward, prediction_error)

    def _select_path(self, root_node: MetaToTNode, exploration_constant: float) -> List[MetaToTNode]:
        path = [root_node]
        current = root_node
        while current.children_ids:
            total_visits = sum(
                self.node_storage[child_id].visit_count
                for child_id in current.children_ids
            )
            best_child = max(
                (self.node_storage[child_id] for child_id in current.children_ids),
                key=lambda n: n.compute_ucb_score(total_visits, exploration_constant),
            )
            path.append(best_child)
            current = best_child
        return path

    def _evaluate_leaf(self, node: MetaToTNode) -> float:
        return 1.0 / (1.0 + node.active_inference_state.free_energy)

    def _select_best_path(self, root_node: MetaToTNode) -> List[str]:
        if not root_node.children_ids:
            return [root_node.node_id]
        best_node = max(
            (self.node_storage[child_id] for child_id in root_node.children_ids),
            key=lambda n: n.value_estimate,
        )
        path = [root_node.node_id, best_node.node_id]
        while best_node.children_ids:
            best_node = max(
                (self.node_storage[cid] for cid in best_node.children_ids),
                key=lambda n: n.value_estimate,
            )
            path.append(best_node.node_id)
        return path

    async def _generate_candidates(
        self,
        node: MetaToTNode,
        domain: str,
        context: Dict[str, Any],
        config: MetaToTConfig,
    ) -> List[str]:
        if not config.use_llm:
            return self._fallback_candidates(node, domain)

        prompt = (
            "Generate concise reasoning branches for a Meta-ToT system. "
            f"Domain: {domain}. Problem: {node.thought_content}. "
            "Return a JSON array of short branch descriptions."
        )
        try:
            response = await chat_completion(
                messages=[{"role": "user", "content": prompt}],
                system_prompt="Return a JSON array of strings only.",
                model=config.llm_model,
                max_tokens=256,
            )
            candidates = self._parse_candidates(response, config.branching_factor)
            if candidates:
                return candidates
        except Exception as exc:
            logger.warning(f"Meta-ToT LLM candidate generation failed: {exc}")
        return self._fallback_candidates(node, domain)

    def _fallback_candidates(self, node: MetaToTNode, domain: str) -> List[str]:
        base = node.thought_content[:160]
        return [
            f"{domain.title()} branch: {base}",
            f"{domain.title()} alternative: {base}",
            f"{domain.title()} refinement: {base}",
        ]

    def _parse_candidates(self, response: str, branching_factor: int) -> List[str]:
        cleaned = response.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.strip("`").replace("json", "").strip()
        try:
            data = json.loads(cleaned)
            if isinstance(data, list):
                return [str(item).strip() for item in data if str(item).strip()]
        except json.JSONDecodeError:
            pass
        lines = [line.strip("- ") for line in cleaned.splitlines() if line.strip()]
        return lines[: branching_factor]

    def _domain_to_node_type(self, domain: str) -> MetaToTNodeType:
        mapping = {
            "explore": MetaToTNodeType.EXPLORATION,
            "challenge": MetaToTNodeType.CHALLENGE,
            "evolve": MetaToTNodeType.EVOLUTION,
            "integrate": MetaToTNodeType.INTEGRATION,
        }
        return mapping.get(domain, MetaToTNodeType.LEAF)

    def _inherit_state(self, node: MetaToTNode) -> ActiveInferenceState:
        return ActiveInferenceState(
            beliefs=node.active_inference_state.beliefs.copy(),
            prediction_updates=node.active_inference_state.prediction_updates.copy(),
            precision=node.active_inference_state.precision,
            reasoning_level=node.active_inference_state.reasoning_level + 1,
            parent_state_id=node.active_inference_state.state_id,
        )

    def _generate_actions(self, root_node: MetaToTNode) -> List[str]:
        if not root_node.children_ids:
            return []
        return [self.node_storage[cid].thought_content for cid in root_node.children_ids]

    def _node_to_trace(self, node: MetaToTNode) -> MetaToTNodeTrace:
        return MetaToTNodeTrace(
            node_id=node.node_id,
            parent_id=node.parent_id,
            depth=node.depth,
            node_type=node.node_type.value,
            cpa_domain=node.cpa_domain,
            thought=node.thought_content,
            score=node.score,
            visit_count=node.visit_count,
            value_estimate=node.value_estimate,
            prediction_error=node.active_inference_state.prediction_error,
            free_energy=node.active_inference_state.free_energy,
            children_ids=node.children_ids,
        )

    async def _update_basins(self, problem: str, context: Dict[str, Any], best_path: List[str]) -> None:
        summary = problem
        if best_path:
            summary = f"{problem} | Selected path: {best_path[-1]}"
        try:
            router = get_memory_basin_router()
            await router.route_memory(summary, memory_type=MemoryType.STRATEGIC, source_id="meta_tot")
        except Exception as exc:
            logger.warning(f"Meta-ToT basin update skipped: {exc}")


_meta_tot_engine: Optional[MetaToTEngine] = None


def get_meta_tot_engine() -> MetaToTEngine:
    global _meta_tot_engine
    if _meta_tot_engine is None:
        _meta_tot_engine = MetaToTEngine()
    return _meta_tot_engine
