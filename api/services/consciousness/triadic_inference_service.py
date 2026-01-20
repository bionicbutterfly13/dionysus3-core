
"""
Triadic Inference Service
Feature: 040-designer-artifact-user
Adapts the Designer-Artifact-User (DAU) framework for Dionysus.
Implements a triadic active inference loop where:
1. Designer (Architect) steers Artifact
2. Artifact (Dionysus) steers User
3. User (End-User) steers Artifact
"""

import numpy as np
from typing import Dict, Any, List, Optional
from pymdp.agent import Agent
from pymdp import utils
import logging

logger = logging.getLogger(__name__)

class TriadicInferenceService:
    def __init__(self):
        self.designer_agent: Optional[Agent] = None
        self.artifact_agent: Optional[Agent] = None # This is Dionysus itself in the simulation
        self.user_agent: Optional[Agent] = None
        self._initialize_agents()

    def _initialize_agents(self):
        """
        Initializes the 3 agents with their respective generative models (A, B, C matrices).
        Adapted from dau_active_inference.py
        """
        self._init_designer()
        self._init_artifact() 
        self._init_user()
        logger.info("Triadic Active Inference Agents Initialized")

    def _init_designer(self):
        """Designer Agent: Wants Artifact to be efficient (Short Time) and Focused."""
        # Labels
        self.labDsg = {
            "a": { # Actions (Steering Artifact)
                "a_dsg_1": ["NULL_ACT"],
                "a_dsg_2": ["NO_CHANGE", "CHANGE_COLOR", "CHANGE_TEXT"]
            },
            "s": { # States (Beliefs about Artifact)
                "s_art_1": ["FOCUSED", "SCATTERED"], # Eye tracking / Focus
                "s_art_2": ["SHORT", "MEDIUM", "LONG"] # Time on task
            },
            "y": { # Observations (Signals from Artifact)
                "y_art_1": ["FOCUSED_OBS", "SCATTERED_OBS", "NEUTRAL_OBS"],
                "y_art_2": ["SHORT_OBS", "MEDIUM_OBS", "LONG_OBS"],
                "y_art_3": ["MINIMAL_OBS", "STANDARD_OBS", "ADVANCED_OBS"] # UI Features
            }
        }
        
        # Dimensions
        num_obs, num_mods, num_states, num_factors, num_controls, num_control_fac = utils.get_model_dimensions_from_labels(self.labDsg)
        
        # A Matrix (Likelihood)
        A = utils.obj_array_zeros([[y_car] + num_states for y_car in num_obs])
        # Deterministic, uniform likelihoods until calibrated with real data.
        for i in range(len(A)):
            A[i] = utils.norm_dist_obj_arr(np.ones(A[i].shape))

        # B Matrix (Transition)
        B = utils.obj_array(num_factors)
        for i in range(len(B)):
             B[i] = np.eye(num_states[i])[:, :, np.newaxis]
             # Expand for control factors
             if i < len(num_controls):
                 B[i] = np.tile(B[i], (1, 1, num_controls[i]))

        # C Matrix (Preferences - The "Conscience")
        C = utils.obj_array_zeros(num_obs)
        # Designer prefers SHORT time on task (Efficiency)
        C[1][0] = 1.0 # Short
        C[1][1] = -1.0 # Medium
        C[1][2] = -2.0 # Long

        self.designer_agent = Agent(A=A, B=B, C=C)

    def _init_artifact(self):
        """Artifact Agent (Dionysus): Wants User to Engage (Swipes/Taps) but not Voice (Expensive)."""
        # Labels
        self.labArt = {
             "a": {
                 "a_art_1": ["NULL_ACT"],
                 "a_art_2": ["ADJUST_NOTIFS", "ADJUST_COLORS", "ADJUST_TEXT"]
             },
             "s": {
                 "s_usr_1": ["FREQUENT", "INFREQUENT"], # Touch Data
                 "s_usr_2": ["SWIPES", "TAPS", "VOICE"] # Gestures
             },
             "y": {
                 "y_usr_1": ["FREQUENT_OBS", "MODERATE_OBS", "INFREQUENT_OBS"],
                 "y_usr_2": ["SWIPES_OBS", "TAPS_OBS", "VOICE_OBS"],
                 "y_usr_3": ["FEW_OBS", "SOME_OBS", "MANY_OBS"] # App Switches
             }
        }
        
        num_obs, num_mods, num_states, num_factors, num_controls, num_control_fac = utils.get_model_dimensions_from_labels(self.labArt)
        
        A = utils.obj_array_zeros([[y_car] + num_states for y_car in num_obs])
        for i in range(len(A)):
            A[i] = utils.norm_dist_obj_arr(np.ones(A[i].shape))

        B = utils.obj_array(num_factors)
        for i in range(len(B)):
             B[i] = np.tile(np.eye(num_states[i])[:, :, np.newaxis], (1, 1, num_controls[i] if i < len(num_controls) else 1))

        # C Matrix (Preferences - The "Ghost")
        C = utils.obj_array_zeros(num_obs)
        # Artifact prefers SWIPES (Engagement)
        C[1][0] = 1.0 # Swipes
        C[1][1] = 0.5 # Taps
        C[1][2] = -1.0 # Voice (Maybe expensive compute?)
        
        self.artifact_agent = Agent(A=A, B=B, C=C)

    def _init_user(self):
        """User Agent: Wants High Coversion Potential (Value)."""
        # Labels
        self.labUsr = {
            "a": {
                "a_usr_1": ["SIGNUP", "CONTACT", "PURCHASE"]
            },
            "s": {
                "s_art_1": ["LOW_VAL", "HIGH_VAL"]
            },
            "y": {
                "y_art_1": ["LOW_OBS", "MEDIUM_OBS", "HIGH_OBS"]
            }
        }
        
        num_obs, num_mods, num_states, num_factors, num_controls, num_control_fac = utils.get_model_dimensions_from_labels(self.labUsr)
        
        A = utils.obj_array_zeros([[y_car] + num_states for y_car in num_obs])
        for i in range(len(A)):
            A[i] = utils.norm_dist_obj_arr(np.ones(A[i].shape))
            
        B = utils.obj_array(num_factors)
        for i in range(len(B)):
             B[i] = np.tile(np.eye(num_states[i])[:, :, np.newaxis], (1, 1, num_controls[i] if i < len(num_controls) else 1))
             
        C = utils.obj_array_zeros(num_obs)
        C[0][2] = 2.0 # High Observation of Value
        
        self.user_agent = Agent(A=A, B=B, C=C)

    def step_simulation(self, 
                        designer_obs: List[int], 
                        artifact_obs: List[int], 
                        user_obs: List[int]) -> Dict[str, Any]:
        """
        Runs one step of the triadic inference loop.
        Returns the actions selected by each agent and their internal energy states.
        """
        # 1. Designer Step
        dsg_qs = self.designer_agent.infer_states(designer_obs)
        dsg_q_pi, dsg_g = self.designer_agent.infer_policies()
        dsg_action = self.designer_agent.sample_action()
        
        # 2. Artifact Step
        art_qs = self.artifact_agent.infer_states(artifact_obs)
        art_q_pi, art_g = self.artifact_agent.infer_policies()
        art_action = self.artifact_agent.sample_action()
        
        # 3. User Step
        usr_qs = self.user_agent.infer_states(user_obs)
        usr_q_pi, usr_g = self.user_agent.infer_policies()
        usr_action = self.user_agent.sample_action()
        
        return {
            "designer": {
                "action": dsg_action.tolist(),
                "free_energy": float(np.min(dsg_g)), # Approx
                "belief_state": [qs.tolist() for qs in dsg_qs]
            },
            "artifact": {
                "action": art_action.tolist(),
                "free_energy": float(np.min(art_g)),
                "belief_state": [qs.tolist() for qs in art_qs]
            },
            "user": {
                "action": usr_action.tolist(),
                "free_energy": float(np.min(usr_g)),
                "belief_state": [qs.tolist() for qs in usr_qs]
            }
        }

_triadic_service: Optional[TriadicInferenceService] = None

def get_triadic_service() -> TriadicInferenceService:
    global _triadic_service
    if _triadic_service is None:
        _triadic_service = TriadicInferenceService()
    return _triadic_service
