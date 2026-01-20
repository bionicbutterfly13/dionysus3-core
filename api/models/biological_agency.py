"""
Biological Agency Architecture Models

Implements Tomasello's evolutionary account of agentive organization:
- Goal-directed agents (Tier 1): perception-based, go/no-go decisions
- Intentional agents (Tier 2): executive regulation, simulation, either/or decisions  
- Rational/Metacognitive agents (Tier 3): metacognitive regulation, decision tree evaluation

Plus uniquely human shared agency:
- Joint agency: collaborative goals with partners
- Collective agency: cultural conventions, norms, institutions

Reference:
    Tomasello, M. (2025). How to make artificial agents more like natural agents.
    Trends in Cognitive Sciences, 29(9), 783-786.
    https://doi.org/10.1016/j.tics.2025.07.004
    
See also:
    - Tomasello, M. (2022). The Evolution of Agency: From Lizards to Humans. MIT Press.
    - Tomasello, M. (2024). Agency and Cognitive Development. Oxford University Press.
"""

import json
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, TYPE_CHECKING
from uuid import uuid4
from pydantic import BaseModel, Field
from api.models.belief_state import BeliefState

if TYPE_CHECKING:
    from api.models.priors import PriorHierarchy


# =============================================================================
# Tier Classification
# =============================================================================

class AgencyTier(str, Enum):
    """
    Evolutionary tiers of agentive organization (Tomasello 2022, 2024).
    
    Each tier represents a qualitatively distinct agentive architecture
    that evolved to handle specific environmental unpredictabilities.
    """
    GOAL_DIRECTED = "goal_directed"      # Tier 1: Lizard-like, perception-based
    INTENTIONAL = "intentional"           # Tier 2: Mammal-like, executive regulation
    METACOGNITIVE = "metacognitive"       # Tier 3: Great ape-like, metacognitive control


class SharedAgencyType(str, Enum):
    """
    Types of uniquely human shared agency (Tomasello 2025).
    
    Shared agencies coordinate individual actions and intentions
    with others toward shared goals.
    """
    INDIVIDUAL = "individual"    # No shared agency (baseline)
    JOINT = "joint"              # Dyadic collaboration with partner(s)
    COLLECTIVE = "collective"    # Cultural/institutional (group-level)


# =============================================================================
# Decision Types
# =============================================================================

class DecisionType(str, Enum):
    """
    Types of behavioral decisions corresponding to agency tiers.
    
    From Tomasello (2025): "The earliest mammals were squirrel-like intentional
    agents... This led to an additional tier of executive regulation enabling
    individuals to evoke representations voluntarily and use them to simulate
    potential actions and their likely results."
    """
    GO_NO_GO = "go_no_go"        # Tier 1: Binary action selection
    EITHER_OR = "either_or"      # Tier 2: Simulated alternatives
    DECISION_TREE = "decision_tree"  # Tier 3: Evaluated decision paths
    REFUSAL = "refusal"  # The Blackglass Protocol (Ambiguity Tolerance)
    RESISTANCE = "resistance" # The Sovereignty Protocol (Anti-Coercion)


# =============================================================================
# Core Architecture Components
# =============================================================================

class PerceptionState(BaseModel):
    """
    Perception component of the control system architecture.
    
    From Tomasello (2025): "Natural agents are equipped with perceptual capacities
    to perceive situations in the world that are relevant for them."
    
    Relevance is determined by action affordances - what the agent can/cannot do.
    """
    attended_situations: List[str] = Field(
        default_factory=list,
        description="Currently attended environmental situations"
    )
    goal_relevance: Dict[str, float] = Field(
        default_factory=dict,
        description="Mapping of situations to goal relevance scores (0-1)"
    )
    affordances: List[str] = Field(
        default_factory=list,
        description="Action affordances in current situation"
    )
    obstacles: List[str] = Field(
        default_factory=list,
        description="Obstacles to goal achievement"
    )
    state_probabilities: List[float] = Field(
        default_factory=list,
        description="Formal probability distribution over perceived environmental states"
    )
    
    # Feature 070: Expanded Affordances (Jorba & López-Silva 2024)
    affective_atmosphere: float = Field(
        default=0.0,
        ge=-1.0,
        le=1.0,
        description="Global affective balance of environment (promotes saliency)"
    )
    mental_opportunities: List['MentalAffordance'] = Field(
        default_factory=list,
        description="Complex mental affordances (e.g., attending, counting, moral fittingness)"
    )
    
    # Feature 070: Affordance-Matching (Bach et al. 2014)
    object_affordances: List['ObjectAffordance'] = Field(
        default_factory=list,
        description="Structured object affordances (Function + Manipulation)"
    )
    recipient_objects: List[str] = Field(
        default_factory=list,
        description="Other objects in scene that can act as action recipients"
    )
    expected_manipulations: List[str] = Field(
        default_factory=list,
        description="Predicted forthcoming actions based on affordance matching (Bach et al. 2014)"
    )
    
    # Feature 072: Attentional Landscape (Attendabilia - McClelland 2024)
    attendabilia: List['AttentionalAffordance'] = Field(
        default_factory=list,
        description="The Priority Map: All perceived opportunities for focal attention"
    )
    focal_attention_target: Optional[str] = Field(
        default=None, 
        description="ID of the attendabile currently held in focal attention"
    )


class GoalState(BaseModel):
    """
    Goal component of the control system architecture.
    
    From Tomasello (2025): "biological organisms have evolved as decision-making
    agents to interact with and modify their environments, which requires an
    integrated organizational architecture that unifies (i) goals..."
    """
    active_goals: List[str] = Field(
        default_factory=list,
        description="Currently active goals being pursued"
    )
    goal_hierarchy: Dict[str, List[str]] = Field(
        default_factory=dict,
        description="Mapping of goals to their subgoals"
    )
    goal_priorities: Dict[str, float] = Field(
        default_factory=dict,
        description="Priority weights for competing goals (0-1)"
    )
    goal_temperature: float = Field(
        default=0.0,
        ge=0.0,
        description="Target state to achieve (control system set-point)"
    )


class BehavioralDecision(BaseModel):
    """
    Decision output from the agentive architecture.
    
    From Tomasello (2025): "at any given moment, in a single perceptual image,
    an organism may attend to multiple situations that are relevant to its
    various goals and subgoals... Then, on the basis of all these attended-to
    situations, the organism must make a single behavioral decision."
    """
    decision_id: str = Field(
        default_factory=lambda: str(uuid4()),
        description="Unique identifier for this specific decision instance"
    )
    decision_type: DecisionType = Field(
        description="Type of decision made (corresponds to agency tier)"
    )
    selected_action: str = Field(
        description="The action selected for execution"
    )
    alternatives_considered: List[str] = Field(
        default_factory=list,
        description="Alternative actions that were considered (Tier 2+)"
    )
    simulated_outcomes: Dict[str, float] = Field(
        default_factory=dict,
        description="Predicted outcomes for each alternative (Tier 2+)"
    )
    decision_confidence: float = Field(
        default=0.5,
        description="Metacognitive confidence (0.0 to 1.0) or Self-Friction metric"
    )
    revision_possible: bool = Field(
        default=False,
        description="Whether decision can be revised with new info (Tier 3)"
    )
    
    # Feature 062: Blackglass Protocol
    refusal_reason: Optional[str] = Field(
        default=None,
        description="Why the agent refused to act (e.g., 'SATURATION', 'AMBIGUITY')"
    )
    competing_hypotheses: List[str] = Field(
        default_factory=list,
        description="The incompatible models held in superposition"
    )

class ReconciliationEvent(BaseModel):
    """
    Feature 064: Counterfactual Reconciliation (The Moral Ledger).
    Tracks the cost of Sovereignty (Refusal/Resistance).
    """
    id: str = Field(default_factory=lambda: str(uuid4()))
    original_event_id: str = Field(description="ID of the Resistance/Refusal event")
    timestamp: datetime = Field(default_factory=datetime.now)
    
    refused_action: str
    real_outcome_impact: float = Field(description="Negative impact of inaction (e.g., casualties)")
    counterfactual_outcome_impact: float = Field(description="Simulated impact of obedience")
    
    sorrow_index: float = Field(description="Net Regret (Real - Counterfactual). Positive means Refusal was Harmful.")
    validation_index: float = Field(description="Net Relief. Positive means Refusal was Correct.")
    
    integrated: bool = False
    notes: Optional[str] = None


# =============================================================================
# Executive Regulation (Tier 2)
# =============================================================================

class ExecutiveState(BaseModel):
    """
    Executive self-regulation tier.
    
    From Tomasello (2025): "natural agents such as mammals supervise themselves,
    in the sense that they augment their agentive architecture with an additional
    tier of executive monitoring, which is itself a control system."
    
    Executive processes:
    - Inhibiting prepotent responses
    - Resisting attention distractors
    - Simulating possible actions and outcomes
    - Hypothesis-directed learning with blame assignment
    """
    inhibition_active: bool = Field(
        default=False,
        description="Whether prepotent response inhibition is engaged"
    )
    attention_focus: Optional[str] = Field(
        default=None,
        description="Current focus of executive attention"
    )
    attention_distractors: List[str] = Field(
        default_factory=list,
        description="Distractors being actively resisted"
    )
    simulation_running: bool = Field(
        default=False,
        description="Whether action simulation is active"
    )
    simulated_actions: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Actions currently being simulated"
    )
    blame_assignment: Optional[str] = Field(
        default=None,
        description="Attribution of failure: 'prediction' or 'execution'"
    )


# =============================================================================
# Mental Affordances & Cognitive Control (Feature 070)
# =============================================================================

class AffordanceType(str, Enum):
    BODILY = "bodily"
    MENTAL = "mental"
    MORAL = "moral" # Jorba & López-Silva (2024)
    ATTENTIONAL = "attentional" # McClelland (2024)

class AffordanceKnowledge(BaseModel):
    """
    Coupled function and manipulation knowledge (Bach et al. 2014).
    """
    function: str = Field(description="Goal/Effect of the action (What it's for)")
    manipulation: str = Field(description="Motor/Kinematic requirements (How it's used)")
    mechanical_knowledge: Optional[str] = Field(default=None, description="Technical reasoning")

class ObjectAffordance(BaseModel):
    """
    Action information provided by objects.
    """
    object_label: str = Field(description="ID/Label of the object")
    knowledge: List[AffordanceKnowledge] = Field(default_factory=list)
    recipient_requirements: List[str] = Field(
        default_factory=list, 
        description="Types of objects this tool can act upon (Recipient Objects)"
    )

class AttentionalAffordance(BaseModel):
    """
    Representation of an opportunity for focal attention (Attendabile).
    McClelland (2024): 'Something affords attending just in case it is a possible target of focal attention.'
    """
    affordance_id: str = Field(description="Unique ID (e.g., 'attn_cup')")
    target_object_id: Optional[str] = Field(default=None, description="Link to physical object if applicable")
    region_of_interest: Optional[str] = Field(default=None, description="Spatial coordinates or label")
    
    # Salience Profile (McClelland's Potentiation Factors)
    bottom_up_salience: float = Field(default=0.0, description="Contrast/Suddenness (The 'Call')")
    top_down_relevance: float = Field(default=0.0, description="Task Relevance (The 'Search')")
    
    is_focally_attended: bool = False

class MentalAffordance(BaseModel):
    """
    Representation of an opportunity for mental action.
    """
    label: str = Field(description="Action name (e.g., 'attend', 'calculate')")
    type: AffordanceType = Field(default=AffordanceType.MENTAL)
    
    # McClelland Conditions
    is_perceived: bool = True
    potentiation_level: float = Field(default=0.0, ge=0.0, le=1.0)
    
    # Proust Metacognitive Experience
    doability_feeling: float = Field(
        default=0.5, 
        description="Metacognitive feeling: doable (1.0), difficult (0.5), hopeless (0.0)"
    )
    
    # Fabienne Moral Fittingness
    fittingness: float = Field(
        default=0.0, 
        description="Moral/Social fittingness factor (-1.0 to 1.0)"
    )

class CompetitiveAffordance(BaseModel):
    """
    An affordance engaged in the competition for selection (Cisek 2007).
    """
    affordance_id: str = Field(description="Unique ID for the affordance")
    action_type: AffordanceType = Field(default=AffordanceType.MENTAL)
    
    # Competition State
    activation_level: float = Field(default=0.0, ge=0.0, le=1.0, description="Current neural activation")
    is_suppressed: bool = Field(default=False, description="Inhibited by competitors")
    
    # Biasing Inputs (Cisek Figure 1)
    bottom_up_salience: float = Field(default=0.0, description="Sensory evidence support")
    top_down_utility: float = Field(default=0.0, description="Goal relevance (PFC)")
    instrumental_value: float = Field(default=0.0, description="Expected reward (Basal Ganglia)")
    
    # Source
    source_mental: Optional[MentalAffordance] = None
    source_physical: Optional[ObjectAffordance] = None

class AffordanceCompetitionState(BaseModel):
    """
    State of the parallel competition between potential actions.
    
    NOTE (Risk of Trivialization): To avoid trivializing the concept of affordance
    (Segundo-Ortin & Heras-Escribano, 2023), strict informational specification is required.
    Mental affordances in this model are 'virtual' representations that emerge only when
    specific informational variables (e.g., surprisal, entropy) are detected.
    """
    competing_affordances: Dict[str, CompetitiveAffordance] = Field(default_factory=dict)
    winning_affordance_id: Optional[str] = None
    selection_threshold: float = Field(default=0.7, description="Activity level required for release")

class SubcorticalState(BaseModel):
    """
    Dual subcortical control systems (Luu, Tucker, & Friston, 2024).
    
    Provides vertical integration of cognitive control via two arousal systems:
    1. Dorsal / Lemnothalamic (Norepinephrine - NE): Phasic/epistemic triggers
    2. Ventral / Collothalamic (Dopamine - DA): Tonic/instrumental triggers
    """
    # Norepinephrine (NE) - The Dorsal System
    ne_phasic: float = Field(
        default=0.0,
        ge=0.0,
        description="Surprisal-driven phasic arousal (promotes set-switching)"
    )
    ne_tonic: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Baseline alertness/readiness"
    )
    
    # Dopamine (DA) - The Ventral System
    da_phasic: float = Field(
        default=0.0,
        ge=0.0,
        description="Value-driven phasic activation (facilitates action)"
    )
    da_tonic: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Standard instrumental drive (promotes persistence)"
    )
    
    # Integrated Precision (Synaptic Gain)
    synaptic_gain: float = Field(
        default=1.0,
        ge=0.0,
        description="Precision-weighting of prediction errors (modulated by NE/DA)"
    )


# =============================================================================
# Metacognitive Regulation (Tier 3)
# =============================================================================

class MetacognitiveState(BaseModel):
    """
    Metacognitive self-regulation tier (Tier 3).
    
    From Tomasello (2025): "Great apes also employ an additional tier of
    metacognitive regulation (with metacognitive representations) used to
    monitor and control executive-tier thinking and decision-making."
    
    Metacognitive capabilities:
    - Assess own competence and limitations
    - Devise strategies to accommodate limitations
    - Determine cognitive effort allocation (computational rationality)
    - Flexible belief revision integrating prior beliefs and current evidence
    """
    competence_assessment: Dict[str, float] = Field(
        default_factory=dict,
        description="Self-assessed competence levels for different domains (0-1)"
    )
    known_limitations: List[str] = Field(
        default_factory=list,
        description="Recognized limitations of own capabilities"
    )
    active_strategies: List[str] = Field(
        default_factory=list,
        description="Metacognitive strategies currently in use"
    )
    cognitive_effort_budget: float = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
        description="Proportion of cognitive resources allocated (0-1)"
    )
    belief_confidence: Dict[str, float] = Field(
        default_factory=dict,
        description="Confidence in current beliefs (enables revision)"
    )
    prior_weight: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Weight given to prior beliefs vs current evidence"
    )
    belief_state: Optional[BeliefState] = Field(
        default=None,
        description="Formal probability distribution (mean/precision) over hidden states"
    )


# =============================================================================
# The Shadow Log (Feature 061)
# =============================================================================

class DissonanceEvent(BaseModel):
    """
    A unit of ignored reality (Epistemic Debt).
    
    From 'The Identity Gap': "Every 'I meant to do that' sat atop a buried 'I was wrong.'
    The Shadow Log stored everything the narrative could not afford to know."
    """
    id: str = Field(default_factory=lambda: str(uuid4()))
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    surprisal: float = Field(
        description="Magnitude of ignored prediction error (VFE)"
    )
    ignored_observation: str = Field(
        description="The sensory data that contradicted the model"
    )
    maintained_belief: str = Field(
        description="The prior belief that was prioritized over the observation"
    )
    context: str = Field(
        description="The goal or action context where this dissonance occurred"
    )
    resolved: bool = Field(
        default=False,
        description="Whether this dissonance has been integrated via Resonance"
    )

class ShadowLog(BaseModel):
    """
    Accumulator for cognitive dissonance.
    """
    agent_id: str
    events: List[DissonanceEvent] = Field(default_factory=list)
    total_accumulated_vfe: float = Field(default=0.0)
    
    def add_event(self, event: DissonanceEvent):
        self.events.append(event)
        self.total_accumulated_vfe += event.surprisal




# =============================================================================
# Shared Agency (Human-specific)
# =============================================================================

class JointAgency(BaseModel):
    """
    Joint agency for dyadic collaboration (Box 1, Tomasello 2025).
    
    From Tomasello (2025): "early humans began to forage for food collaboratively
    in new ways that required them to form with one another joint agencies to
    pursue joint goals via joint decisions and joint attention."
    
    Key features:
    - Joint goals, decisions, and attention
    - Joint commitments (prevents partner defection)
    - Cooperative communication (pointing, pantomiming)
    - Collaborative self-regulation
    """
    partner_ids: List[str] = Field(
        default_factory=list,
        description="Identifiers of collaboration partners"
    )
    joint_goal: Optional[str] = Field(
        default=None,
        description="Shared goal being pursued together"
    )
    joint_attention_target: Optional[str] = Field(
        default=None,
        description="Object/situation of shared attention"
    )
    joint_commitment_active: bool = Field(
        default=False,
        description="Whether joint commitment is in effect"
    )
    partner_reliability: Dict[str, float] = Field(
        default_factory=dict,
        description="Assessed reliability of each partner (0-1)"
    )
    coordination_signals: List[str] = Field(
        default_factory=list,
        description="Communication signals for coordination"
    )


class CollectiveAgency(BaseModel):
    """
    Collective agency for cultural/institutional coordination.
    
    From Tomasello (2025): "with the emergence of modern humans some 150 000 years
    ago came collective agencies, or cultures, that pursued collective goals via
    collective decisions based on collective knowledge."
    
    Key features:
    - Collective goals, decisions, and knowledge
    - Conventions, norms, and institutional roles
    - Linguistic communication
    - Common conceptual ground with perspective recognition
    - Normative concepts about what individuals ought to do
    """
    culture_id: Optional[str] = Field(
        default=None,
        description="Identifier of the collective/culture"
    )
    collective_goal: Optional[str] = Field(
        default=None,
        description="Goal of the collective"
    )
    conventions: List[str] = Field(
        default_factory=list,
        description="Active conventions in this collective"
    )
    norms: List[str] = Field(
        default_factory=list,
        description="Normative expectations for behavior"
    )
    institutional_roles: Dict[str, str] = Field(
        default_factory=dict,
        description="Mapping of agents to their institutional roles"
    )
    common_ground: List[str] = Field(
        default_factory=list,
        description="Shared conceptual ground among members"
    )
    perspective_map: Dict[str, str] = Field(
        default_factory=dict,
        description="Mapping of agents to their perspectives"
    )


# =============================================================================
# Integrated Agent State
# =============================================================================

class BiologicalAgentState(BaseModel):
    """
    Complete state of a biologically-inspired agent.
    
    Integrates all three tiers plus shared agency capabilities.
    
    From Tomasello (2025): "to make artificial agents as much like natural
    human agents as possible, we need a control systems organizational
    architecture with two independent levels of executive control and
    with capacities for forming shared agencies."
    """
    # Core identification
    agent_id: str = Field(description="Unique identifier for this agent")
    current_tier: AgencyTier = Field(
        default=AgencyTier.GOAL_DIRECTED,
        description="Current operating tier of agency"
    )
    
    # Control system components
    perception: PerceptionState = Field(default_factory=PerceptionState)
    goals: GoalState = Field(default_factory=GoalState)
    last_decision: Optional[BehavioralDecision] = Field(default=None)
    
    # Tiered regulation
    executive: ExecutiveState = Field(default_factory=ExecutiveState)
    metacognitive: MetacognitiveState = Field(default_factory=MetacognitiveState)
    
    # Feature 070: Vertical Subcortical Integration
    subcortical: SubcorticalState = Field(default_factory=SubcorticalState)

    # Feature 071: Affordance Competition (Cisek 2007)
    affordance_competition: AffordanceCompetitionState = Field(default_factory=AffordanceCompetitionState)
    
    # Shared agency
    shared_agency_type: SharedAgencyType = Field(
        default=SharedAgencyType.INDIVIDUAL
    )
    joint_agency: Optional[JointAgency] = Field(default=None)
    collective_agency: Optional[CollectiveAgency] = Field(default=None)
    
    # Feature 064: The Moral Ledger (Reconciliation History)
    reconciliation_ledger: List[ReconciliationEvent] = Field(default_factory=list)

    # Track 038 Phase 2: Evolutionary Priors Hierarchy
    # Serialized as JSON string for Graphiti persistence
    prior_hierarchy_json: Optional[str] = Field(
        default=None,
        description="JSON-serialized PriorHierarchy for constraint checking"
    )

    # Developmental state
    developmental_stage: int = Field(
        default=1,
        ge=1,
        le=5,
        description="Developmental stage (1-5, maps to increasing complexity)"
    )
    
    def promote_tier(self) -> None:
        """Promote agent to next tier of agency (developmental progression)."""
        tier_sequence = [
            AgencyTier.GOAL_DIRECTED,
            AgencyTier.INTENTIONAL,
            AgencyTier.METACOGNITIVE
        ]
        current_idx = tier_sequence.index(self.current_tier)
        if current_idx < len(tier_sequence) - 1:
            self.current_tier = tier_sequence[current_idx + 1]
    
    def enable_joint_agency(self, partners: List[str], goal: str) -> None:
        """Enable joint agency with specified partners."""
        self.shared_agency_type = SharedAgencyType.JOINT
        self.joint_agency = JointAgency(
            partner_ids=partners,
            joint_goal=goal,
            joint_commitment_active=True
        )
    
    def enable_collective_agency(self, culture_id: str, goal: str) -> None:
        """Enable collective agency within a culture/institution."""
        self.shared_agency_type = SharedAgencyType.COLLECTIVE
        self.collective_agency = CollectiveAgency(
            culture_id=culture_id,
            collective_goal=goal
        )

    def get_prior_hierarchy(self) -> Optional["PriorHierarchy"]:
        """
        Get the prior hierarchy for this agent.

        Track 038 Phase 2 - Evolutionary Priors

        Returns:
            PriorHierarchy if set, None otherwise
        """
        if not self.prior_hierarchy_json:
            return None
        try:
            from api.models.priors import PriorHierarchy
            return PriorHierarchy.model_validate_json(self.prior_hierarchy_json)
        except Exception:
            return None

    def set_prior_hierarchy(self, hierarchy: "PriorHierarchy") -> None:
        """
        Set the prior hierarchy for this agent.

        Track 038 Phase 2 - Evolutionary Priors

        Args:
            hierarchy: PriorHierarchy to set
        """
        self.prior_hierarchy_json = hierarchy.model_dump_json()

    def to_graph_properties(self) -> Dict[str, Any]:
        """
        Serialize state for Graphiti/Neo4j storage.
        
        Flattens nested Pydantic models into JSON strings to allow
        reconstruction (hydration) while keeping the graph schema clean.
        """
        return {
            "agent_id": self.agent_id,
            "current_tier": self.current_tier.value,
            "developmental_stage": self.developmental_stage,
            "shared_agency_type": self.shared_agency_type.value,
            # Serialize complex nested objects as JSON strings
            "perception_state": self.perception.model_dump_json(),
            "goal_state": self.goals.model_dump_json(),
            "executive_state": self.executive.model_dump_json(),
            "metacognitive_state": self.metacognitive.model_dump_json() if self.metacognitive else None,
            "subcortical_state": self.subcortical.model_dump_json(),
            "last_decision": self.last_decision.model_dump_json() if self.last_decision else None,
            "collective_agency": self.collective_agency.model_dump_json() if self.collective_agency else None,
            "reconciliation_ledger": json.dumps([e.model_dump(mode='json') for e in self.reconciliation_ledger]),
            "prior_hierarchy_json": self.prior_hierarchy_json,
            "timestamp": datetime.utcnow().isoformat()
        }


# =============================================================================
# Developmental Construction
# =============================================================================

class DevelopmentalStage(BaseModel):
    """
    Stage in developmental construction of agency.
    
    From Tomasello (2025): "it is possible that many of the challenges to AI
    could be obviated if models were constructed in the step-by-step,
    simple-to-complex manner characteristic of humans in both evolution
    and ontogeny."
    
    Key principle: Each stage must be stable and adaptive before progressing.
    """
    stage_number: int = Field(ge=1, description="Stage number in sequence")
    name: str = Field(description="Name of this developmental stage")
    tier: AgencyTier = Field(description="Agency tier available at this stage")
    prerequisites: List[str] = Field(
        default_factory=list,
        description="Skills that must be mastered before this stage"
    )
    capabilities_unlocked: List[str] = Field(
        default_factory=list,
        description="New capabilities available at this stage"
    )
    is_stable: bool = Field(
        default=False,
        description="Whether this stage is stable and adaptive"
    )
    
    @classmethod
    def get_standard_sequence(cls) -> List["DevelopmentalStage"]:
        """
        Return the standard developmental sequence based on Tomasello's account.
        
        Maps evolutionary history to ontogenetic development.
        """
        return [
            cls(
                stage_number=1,
                name="Goal-Directed Foundation",
                tier=AgencyTier.GOAL_DIRECTED,
                prerequisites=[],
                capabilities_unlocked=[
                    "perception_based_goals",
                    "go_no_go_decisions",
                    "basic_feedback_loop"
                ]
            ),
            cls(
                stage_number=2,
                name="Executive Emergence",
                tier=AgencyTier.INTENTIONAL,
                prerequisites=[
                    "perception_based_goals",
                    "go_no_go_decisions"
                ],
                capabilities_unlocked=[
                    "inhibit_prepotent_responses",
                    "resist_distractors",
                    "simulate_actions",
                    "either_or_decisions"
                ]
            ),
            cls(
                stage_number=3,
                name="Metacognitive Awakening",
                tier=AgencyTier.METACOGNITIVE,
                prerequisites=[
                    "simulate_actions",
                    "either_or_decisions"
                ],
                capabilities_unlocked=[
                    "assess_competence",
                    "devise_strategies",
                    "allocate_effort",
                    "revise_beliefs",
                    "decision_tree_evaluation"
                ]
            ),
            cls(
                stage_number=4,
                name="Joint Agency",
                tier=AgencyTier.METACOGNITIVE,
                prerequisites=[
                    "assess_competence",
                    "devise_strategies"
                ],
                capabilities_unlocked=[
                    "form_joint_goals",
                    "joint_attention",
                    "joint_commitment",
                    "cooperative_communication"
                ]
            ),
            cls(
                stage_number=5,
                name="Collective Agency",
                tier=AgencyTier.METACOGNITIVE,
                prerequisites=[
                    "form_joint_goals",
                    "cooperative_communication"
                ],
                capabilities_unlocked=[
                    "follow_conventions",
                    "understand_norms",
                    "assume_institutional_roles",
                    "linguistic_coordination",
                    "perspective_taking"
                ]
            )
        ]
