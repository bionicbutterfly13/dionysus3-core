"""
Biological Agency Service

Implements Tomasello's control systems architecture for natural agents.
Orchestrates the three-tier agentive organization and shared agency capabilities.

Integration with existing Dionysus components:
- HeartbeatAgent (OODA loop) → Control system feedback
- ProceduralMetacognition → Tier 2/3 regulation
- AgencyService → Agency attribution/detection
- ConsciousnessManager → Sub-agent coordination

Reference:
    Tomasello, M. (2025). How to make artificial agents more like natural agents.
    Trends in Cognitive Sciences, 29(9), 783-786.
    https://doi.org/10.1016/j.tics.2025.07.004
"""

import logging
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime

from api.models.biological_agency import (
    AgencyTier,
    SharedAgencyType,
    DecisionType,
    PerceptionState,
    GoalState,
    BehavioralDecision,
    ExecutiveState,
    MetacognitiveState,
    JointAgency,
    CollectiveAgency,
    BiologicalAgentState,
    DevelopmentalStage,
)

logger = logging.getLogger(__name__)


class BiologicalAgencyService:
    """
    Orchestrates the three-tier biological agency architecture.
    
    Core design principles from Tomasello (2025):
    1. Control systems architecture unifying goals, attention, and decisions
    2. Relevance determined by action affordances
    3. Two independent tiers of executive control
    4. Capacity for shared agencies
    5. Developmental construction (simple-to-complex)
    """
    
    def __init__(self):
        """Initialize the biological agency service."""
        self._agents: Dict[str, BiologicalAgentState] = {}
        self._developmental_sequence = DevelopmentalStage.get_standard_sequence()
        self._collective_agencies: Dict[str, CollectiveAgency] = {}
        
    # =========================================================================
    # Agent Lifecycle
    # =========================================================================
    
    def create_agent(
        self, 
        agent_id: str,
        initial_tier: AgencyTier = AgencyTier.GOAL_DIRECTED
    ) -> BiologicalAgentState:
        """
        Create a new biological agent at specified tier.
        
        Following developmental construction principle, agents typically
        start at Tier 1 (goal-directed) and progress through stages.
        
        Args:
            agent_id: Unique identifier for the agent
            initial_tier: Starting tier (default: goal-directed)
            
        Returns:
            New BiologicalAgentState instance
        """
        agent = BiologicalAgentState(
            agent_id=agent_id,
            current_tier=initial_tier,
            developmental_stage=self._tier_to_stage(initial_tier)
        )
        self._agents[agent_id] = agent
        
        logger.info(
            f"Created biological agent {agent_id} at tier {initial_tier.value}"
        )
        return agent
    
    def get_agent(self, agent_id: str) -> Optional[BiologicalAgentState]:
        """Retrieve agent state by ID."""
        return self._agents.get(agent_id)
    
    # =========================================================================
    # Tier 1: Goal-Directed Processing
    # =========================================================================
    
    def process_tier1_decision(
        self,
        agent_id: str,
        perception: PerceptionState,
        goals: GoalState
    ) -> BehavioralDecision:
        """
        Process a Tier 1 (goal-directed) decision.
        
        From Tomasello (2025): "lizard-like goal-directed agents...operated
        with perception-based representations of goal states that they could
        recognize and then pursue using go/no-go behavioral decisions."
        
        This is binary decision-making: either act or don't act.
        No simulation or metacognitive evaluation.
        
        Args:
            agent_id: Agent making the decision
            perception: Current perceptual state
            goals: Current goal state
            
        Returns:
            BehavioralDecision with go/no-go outcome
        """
        agent = self._ensure_agent(agent_id)
        agent.perception = perception
        agent.goals = goals
        
        # Select most relevant affordance for highest priority goal
        selected_action = None
        if perception.affordances and goals.active_goals:
            # Find best affordance-goal match
            best_match = self._match_affordance_to_goal(
                perception.affordances,
                goals.active_goals,
                perception.goal_relevance
            )
            if best_match:
                selected_action = best_match
        
        # Go/no-go decision
        if selected_action and not perception.obstacles:
            decision = BehavioralDecision(
                decision_type=DecisionType.GO_NO_GO,
                selected_action=selected_action,
                decision_confidence=0.5  # Fixed for Tier 1
            )
        else:
            decision = BehavioralDecision(
                decision_type=DecisionType.GO_NO_GO,
                selected_action="no_action",
                decision_confidence=0.5
            )
        
        agent.last_decision = decision
        return decision
    
    # =========================================================================
    # Tier 2: Executive Regulation
    # =========================================================================
    
    def process_tier2_decision(
        self,
        agent_id: str,
        perception: PerceptionState,
        goals: GoalState,
        alternatives: List[str]
    ) -> Tuple[BehavioralDecision, ExecutiveState]:
        """
        Process a Tier 2 (intentional) decision with executive regulation.
        
        From Tomasello (2025): "earliest mammals...led to an additional tier
        of executive regulation enabling individuals to evoke representations
        voluntarily and use them to simulate potential actions and their
        likely results in acts of either/or decision-making."
        
        Key capabilities:
        - Inhibit prepotent responses
        - Resist attention distractors
        - Simulate actions and outcomes
        - Either/or decision-making
        
        Args:
            agent_id: Agent making the decision
            perception: Current perceptual state
            goals: Current goal state
            alternatives: Alternative actions to consider
            
        Returns:
            Tuple of (BehavioralDecision, ExecutiveState)
        """
        agent = self._ensure_agent(agent_id)
        
        if agent.current_tier == AgencyTier.GOAL_DIRECTED:
            # Promote to Tier 2 if needed
            agent.current_tier = AgencyTier.INTENTIONAL
            agent.developmental_stage = 2
        
        agent.perception = perception
        agent.goals = goals
        
        # Engage executive regulation
        executive = ExecutiveState(
            inhibition_active=bool(perception.obstacles),
            attention_focus=goals.active_goals[0] if goals.active_goals else None,
            attention_distractors=perception.obstacles,
            simulation_running=True,
            simulated_actions=[]
        )
        
        # Simulate each alternative
        simulated_outcomes: Dict[str, float] = {}
        for action in alternatives:
            outcome = self._simulate_action(action, perception, goals)
            simulated_outcomes[action] = outcome
            executive.simulated_actions.append({
                "action": action,
                "predicted_outcome": outcome
            })
        
        executive.simulation_running = False
        
        # Either/or selection based on simulation
        if simulated_outcomes:
            best_action = max(simulated_outcomes, key=simulated_outcomes.get)
        else:
            best_action = "no_action"
        
        decision = BehavioralDecision(
            decision_type=DecisionType.EITHER_OR,
            selected_action=best_action,
            alternatives_considered=alternatives,
            simulated_outcomes=simulated_outcomes,
            decision_confidence=0.7
        )
        
        agent.executive = executive
        agent.last_decision = decision
        
        return decision, executive
    
    # =========================================================================
    # Tier 3: Metacognitive Regulation
    # =========================================================================
    
    def process_tier3_decision(
        self,
        agent_id: str,
        perception: PerceptionState,
        goals: GoalState,
        decision_tree: List[Dict[str, Any]]
    ) -> Tuple[BehavioralDecision, MetacognitiveState]:
        """
        Process a Tier 3 (metacognitive) decision with full self-regulation.
        
        From Tomasello (2025): "Great apes also employ an additional tier of
        metacognitive regulation...used to monitor and control executive-tier
        thinking and decision-making."
        
        Key capabilities:
        - Assess own competence and limitations
        - Devise metacognitive strategies
        - Computational rationality (effort allocation)
        - Flexible belief revision
        - Evaluate decision trees (not just alternatives)
        
        Args:
            agent_id: Agent making the decision
            perception: Current perceptual state
            goals: Current goal state
            decision_tree: Tree of possible decision paths
            
        Returns:
            Tuple of (BehavioralDecision, MetacognitiveState)
        """
        agent = self._ensure_agent(agent_id)
        
        if agent.current_tier != AgencyTier.METACOGNITIVE:
            agent.current_tier = AgencyTier.METACOGNITIVE
            agent.developmental_stage = 3
        
        agent.perception = perception
        agent.goals = goals
        
        # Initialize metacognitive state
        metacog = MetacognitiveState(
            cognitive_effort_budget=self._allocate_cognitive_effort(goals),
            prior_weight=0.5  # Balanced prior/evidence weighting
        )
        
        # Assess competence for this decision domain
        domain = goals.active_goals[0] if goals.active_goals else "general"
        metacog.competence_assessment[domain] = self._assess_competence(
            agent, domain
        )
        
        # Identify limitations
        if metacog.competence_assessment.get(domain, 0) < 0.5:
            metacog.known_limitations.append(f"low_competence_{domain}")
            metacog.active_strategies.append("seek_additional_information")
        
        # Evaluate decision tree paths
        path_scores: Dict[str, float] = {}
        for path in decision_tree:
            path_id = path.get("id", str(hash(str(path))))
            path_scores[path_id] = self._evaluate_decision_path(
                path, perception, goals, metacog
            )
        
        # Select best path with metacognitive confidence
        if path_scores:
            best_path_id = max(path_scores, key=path_scores.get)
            best_path = next(
                (p for p in decision_tree if p.get("id") == best_path_id),
                decision_tree[0]
            )
            selected_action = best_path.get("action", "no_action")
            confidence = path_scores[best_path_id]
        else:
            selected_action = "no_action"
            confidence = 0.3
        
        # Update belief confidence
        metacog.belief_confidence["decision_quality"] = confidence
        
        decision = BehavioralDecision(
            decision_type=DecisionType.DECISION_TREE,
            selected_action=selected_action,
            alternatives_considered=[p.get("action", "") for p in decision_tree],
            simulated_outcomes=path_scores,
            decision_confidence=confidence,
            revision_possible=True  # Tier 3 can revise with new info
        )
        
        agent.metacognitive = metacog
        agent.last_decision = decision
        
        return decision, metacog
    
    # =========================================================================
    # Shared Agency
    # =========================================================================
    
    def form_joint_agency(
        self,
        initiator_id: str,
        partner_ids: List[str],
        joint_goal: str
    ) -> JointAgency:
        """
        Form a joint agency between agents.
        
        From Tomasello (2025): "early humans began to forage for food
        collaboratively in new ways that required them to form with one
        another joint agencies to pursue joint goals via joint decisions
        and joint attention."
        
        Joint commitment prevents partner defection.
        
        Args:
            initiator_id: Agent initiating the joint agency
            partner_ids: IDs of partner agents
            joint_goal: Shared goal to pursue
            
        Returns:
            JointAgency configuration
        """
        initiator = self._ensure_agent(initiator_id)
        
        # Verify partners exist
        all_partners = [initiator_id] + partner_ids
        for pid in partner_ids:
            if pid not in self._agents:
                self.create_agent(pid, AgencyTier.METACOGNITIVE)
        
        joint = JointAgency(
            partner_ids=partner_ids,
            joint_goal=joint_goal,
            joint_commitment_active=True,
            partner_reliability={pid: 0.5 for pid in partner_ids}
        )
        
        # Enable joint agency for all participants
        initiator.enable_joint_agency(partner_ids, joint_goal)
        for pid in partner_ids:
            partner = self._agents[pid]
            other_partners = [p for p in all_partners if p != pid]
            partner.enable_joint_agency(other_partners, joint_goal)
        
        logger.info(
            f"Formed joint agency: {initiator_id} + {partner_ids} "
            f"for goal '{joint_goal}'"
        )
        return joint
    
    def create_collective_agency(
        self,
        culture_id: str,
        collective_goal: str,
        conventions: List[str],
        norms: List[str]
    ) -> CollectiveAgency:
        """
        Create a collective agency (culture/institution).
        
        From Tomasello (2025): "with the emergence of modern humans...came
        collective agencies, or cultures, that pursued collective goals via
        collective decisions based on collective knowledge."
        
        Args:
            culture_id: Identifier for this collective
            collective_goal: Goal of the collective
            conventions: Shared conventions
            norms: Normative expectations
            
        Returns:
            CollectiveAgency configuration
        """
        collective = CollectiveAgency(
            culture_id=culture_id,
            collective_goal=collective_goal,
            conventions=conventions,
            norms=norms,
            common_ground=[collective_goal] + conventions
        )
        
        self._collective_agencies[culture_id] = collective
        
        logger.info(
            f"Created collective agency '{culture_id}' "
            f"with goal '{collective_goal}'"
        )
        return collective
    
    def join_collective(
        self,
        agent_id: str,
        culture_id: str,
        role: str
    ) -> None:
        """
        Add an agent to a collective agency with a specific role.
        
        From Tomasello (2025): "Coordinating with the group required mastery
        of its conventions, norms, and institutional roles."
        
        Args:
            agent_id: Agent joining the collective
            culture_id: ID of the collective to join
            role: Institutional role the agent will assume
        """
        agent = self._ensure_agent(agent_id)
        collective = self._collective_agencies.get(culture_id)
        
        if not collective:
            raise ValueError(f"Collective '{culture_id}' not found")
        
        agent.enable_collective_agency(culture_id, collective.collective_goal)
        agent.collective_agency = collective
        collective.institutional_roles[agent_id] = role
        
        logger.info(
            f"Agent {agent_id} joined collective '{culture_id}' as '{role}'"
        )
    
    # =========================================================================
    # Developmental Construction
    # =========================================================================
    
    def advance_development(self, agent_id: str) -> Optional[DevelopmentalStage]:
        """
        Advance agent to next developmental stage if prerequisites are met.
        
        From Tomasello (2025): "it is necessary for each step in the sequence
        to be stable and adaptive in its own right, or else the species or
        organism perishes along the way."
        
        Args:
            agent_id: Agent to advance
            
        Returns:
            New DevelopmentalStage if advanced, None if not ready
        """
        agent = self._ensure_agent(agent_id)
        current_stage_num = agent.developmental_stage
        
        if current_stage_num >= len(self._developmental_sequence):
            logger.info(f"Agent {agent_id} at maximum development")
            return None
        
        next_stage = self._developmental_sequence[current_stage_num]
        
        # Check prerequisites
        mastered = self._get_mastered_capabilities(agent)
        unmet = [
            prereq for prereq in next_stage.prerequisites
            if prereq not in mastered
        ]
        
        if unmet:
            logger.info(
                f"Agent {agent_id} cannot advance: "
                f"unmet prerequisites {unmet}"
            )
            return None
        
        # Advance
        agent.developmental_stage = next_stage.stage_number
        agent.current_tier = next_stage.tier
        
        logger.info(
            f"Agent {agent_id} advanced to stage {next_stage.stage_number}: "
            f"'{next_stage.name}'"
        )
        return next_stage
    
    def get_developmental_status(self, agent_id: str) -> Dict[str, Any]:
        """
        Get developmental status of an agent.
        
        Returns:
            Dictionary with stage info, mastered capabilities, next prereqs
        """
        agent = self._ensure_agent(agent_id)
        current_idx = agent.developmental_stage - 1
        current_stage = self._developmental_sequence[current_idx]
        
        mastered = self._get_mastered_capabilities(agent)
        
        # Get next stage prerequisites
        next_prereqs = []
        if current_idx + 1 < len(self._developmental_sequence):
            next_stage = self._developmental_sequence[current_idx + 1]
            next_prereqs = next_stage.prerequisites
        
        return {
            "agent_id": agent_id,
            "current_stage": current_stage.stage_number,
            "stage_name": current_stage.name,
            "tier": agent.current_tier.value,
            "mastered_capabilities": list(mastered),
            "next_prerequisites": next_prereqs,
            "ready_to_advance": all(p in mastered for p in next_prereqs)
        }
    
    # =========================================================================
    # Integration with Existing Systems
    # =========================================================================
    
    def integrate_ooda_cycle(
        self,
        agent_id: str,
        observe_data: Dict[str, Any],
        orient_analysis: Dict[str, Any],
        decide_context: Dict[str, Any]
    ) -> BehavioralDecision:
        """
        Integrate with the OODA loop from HeartbeatAgent.
        
        Maps OODA phases to biological agency architecture:
        - OBSERVE → PerceptionState
        - ORIENT → GoalState + relevance computation
        - DECIDE → Tier-appropriate decision
        - ACT → Selected action execution
        
        Args:
            agent_id: Agent in the OODA loop
            observe_data: Data from OBSERVE phase
            orient_analysis: Analysis from ORIENT phase
            decide_context: Context for DECIDE phase
            
        Returns:
            BehavioralDecision from appropriate tier
        """
        agent = self._ensure_agent(agent_id)
        
        # Map OBSERVE to PerceptionState
        perception = PerceptionState(
            attended_situations=observe_data.get("situations", []),
            goal_relevance=observe_data.get("relevance", {}),
            affordances=observe_data.get("affordances", []),
            obstacles=observe_data.get("obstacles", [])
        )
        
        # Map ORIENT to GoalState
        goals = GoalState(
            active_goals=orient_analysis.get("active_goals", []),
            goal_hierarchy=orient_analysis.get("goal_hierarchy", {}),
            goal_priorities=orient_analysis.get("goal_priorities", {})
        )
        
        # Select tier-appropriate decision process
        if agent.current_tier == AgencyTier.GOAL_DIRECTED:
            return self.process_tier1_decision(agent_id, perception, goals)
        
        elif agent.current_tier == AgencyTier.INTENTIONAL:
            alternatives = decide_context.get("alternatives", [])
            decision, _ = self.process_tier2_decision(
                agent_id, perception, goals, alternatives
            )
            return decision
        
        else:  # METACOGNITIVE
            decision_tree = decide_context.get("decision_tree", [])
            decision, _ = self.process_tier3_decision(
                agent_id, perception, goals, decision_tree
            )
            return decision
    
    # =========================================================================
    # Private Helpers
    # =========================================================================
    
    def _ensure_agent(self, agent_id: str) -> BiologicalAgentState:
        """Ensure agent exists, creating if necessary."""
        if agent_id not in self._agents:
            return self.create_agent(agent_id)
        return self._agents[agent_id]
    
    def _tier_to_stage(self, tier: AgencyTier) -> int:
        """Map agency tier to developmental stage number."""
        mapping = {
            AgencyTier.GOAL_DIRECTED: 1,
            AgencyTier.INTENTIONAL: 2,
            AgencyTier.METACOGNITIVE: 3
        }
        return mapping.get(tier, 1)
    
    def _match_affordance_to_goal(
        self,
        affordances: List[str],
        goals: List[str],
        relevance: Dict[str, float]
    ) -> Optional[str]:
        """Find best affordance for achieving goals."""
        best_score = 0.0
        best_affordance = None
        
        for affordance in affordances:
            score = relevance.get(affordance, 0.0)
            if score > best_score:
                best_score = score
                best_affordance = affordance
        
        return best_affordance
    
    def _simulate_action(
        self,
        action: str,
        perception: PerceptionState,
        goals: GoalState
    ) -> float:
        """
        Simulate an action and return predicted outcome value.
        
        This is Tier 2 executive simulation capability.
        """
        # Base score from goal relevance
        base_score = perception.goal_relevance.get(action, 0.5)
        
        # Penalize if obstacles present
        obstacle_penalty = 0.1 * len(perception.obstacles)
        
        # Boost if affordance available
        affordance_boost = 0.1 if action in perception.affordances else 0.0
        
        return max(0.0, min(1.0, base_score - obstacle_penalty + affordance_boost))
    
    def _allocate_cognitive_effort(self, goals: GoalState) -> float:
        """
        Allocate cognitive effort based on goal priorities.
        
        From Tomasello (2025): computational rationality - determining
        how much cognitive effort to devote to competing demands.
        """
        if not goals.goal_priorities:
            return 0.5
        
        max_priority = max(goals.goal_priorities.values())
        return min(1.0, max_priority + 0.2)
    
    def _assess_competence(
        self,
        agent: BiologicalAgentState,
        domain: str
    ) -> float:
        """
        Assess agent's competence in a domain.
        
        From Tomasello (2025): metacognitive capability to assess
        own competence and limitations.
        """
        # Use developmental stage as proxy for base competence
        base = agent.developmental_stage / 5.0
        
        # Adjust based on historical performance (if available)
        if domain in agent.metacognitive.competence_assessment:
            historical = agent.metacognitive.competence_assessment[domain]
            return (base + historical) / 2.0
        
        return base
    
    def _evaluate_decision_path(
        self,
        path: Dict[str, Any],
        perception: PerceptionState,
        goals: GoalState,
        metacog: MetacognitiveState
    ) -> float:
        """
        Evaluate a decision tree path.
        
        From Tomasello (2025): Tier 3 capability to evaluate alternative
        possible decision trees and reevaluate decisions with new info.
        """
        action = path.get("action", "")
        expected_outcome = path.get("expected_outcome", 0.5)
        risk = path.get("risk", 0.3)
        
        # Base evaluation
        base_score = self._simulate_action(action, perception, goals)
        
        # Metacognitive adjustments
        effort_factor = metacog.cognitive_effort_budget
        competence = list(metacog.competence_assessment.values())
        avg_competence = sum(competence) / len(competence) if competence else 0.5
        
        # Combine factors
        score = (
            base_score * 0.4 +
            expected_outcome * 0.3 +
            (1 - risk) * 0.2 +
            avg_competence * effort_factor * 0.1
        )
        
        return min(1.0, max(0.0, score))
    
    def _get_mastered_capabilities(
        self,
        agent: BiologicalAgentState
    ) -> set:
        """
        Get set of capabilities the agent has mastered.
        
        Based on current tier and accumulated experience.
        """
        mastered = set()
        
        # Add capabilities from all stages up to current
        for stage in self._developmental_sequence[:agent.developmental_stage]:
            mastered.update(stage.capabilities_unlocked)
        
        return mastered


# Singleton instance
_service_instance: Optional[BiologicalAgencyService] = None


def get_biological_agency_service() -> BiologicalAgencyService:
    """Get the singleton BiologicalAgencyService instance."""
    global _service_instance
    if _service_instance is None:
        _service_instance = BiologicalAgencyService()
    return _service_instance
