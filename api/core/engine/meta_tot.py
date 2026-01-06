from typing import List, Dict, Optional, Any
import asyncio
import uuid
from datetime import datetime
import logging

from api.core.engine.models import ThoughtNode, ReasoningBranch
from api.core.engine.active_inference import get_active_inference_wrapper, ActiveInferenceWrapper

logger = logging.getLogger("dionysus.meta_tot")

class MetaToTEngine:
    """
    The Tree-of-Thought Orchestrator.
    Manages the "Thinking" process by generating multiple branches, scoring them via Active Inference,
    and selecting the optimal path (MCTS/POMCP simulation).
    """
    def __init__(self):
        self.ai_wrapper: ActiveInferenceWrapper = get_active_inference_wrapper()
        self.nodes: Dict[str, ThoughtNode] = {}
        self.root_id: Optional[str] = None
        self.active_goal_vector: List[float] = [] 

    async def initialize_session(self, initial_thought: str, goal_vector: List[float]):
        """
        Starts a new thinking session.
        """
        self.active_goal_vector = goal_vector
        root = ThoughtNode(content=initial_thought, depth=0)
        
        # Score the root (Context setting)
        root.score = await self.ai_wrapper.score_thought(
            root, self.active_goal_vector
        )
        
        self.nodes[root.id] = root
        self.root_id = root.id
        logger.info(f"Initialized Meta-ToT Session: {root.id}")
        return root

    async def expand_node(
        self, 
        parent_id: str, 
        candidate_contents: List[str]
    ) -> List[ThoughtNode]:
        """
        Generates child nodes (branches) from a parent thought.
        """
        parent = self.nodes.get(parent_id)
        if not parent:
            raise ValueError(f"Parent node {parent_id} not found")
            
        new_nodes = []
        for content in candidate_contents:
            child = ThoughtNode(
                content=content,
                parent_id=parent_id,
                depth=parent.depth + 1
            )
            
            # Score the child using real active inference computation
            # ActiveInferenceWrapper handles embedding generation and EFE calculation
            # with precision-weighted prediction errors (FR-003, FR-004)
            child.score = await self.ai_wrapper.score_thought(
                child, self.active_goal_vector
            )
            
            self.nodes[child.id] = child
            parent.children_ids.append(child.id)
            new_nodes.append(child)
            
        return new_nodes

    async def select_best_branch(self, current_node_id: str) -> Optional[ThoughtNode]:
        """
        Selects the best child node based on minimal Expected Free Energy (EFE).
        This effectively implements the "Selection" phase of MCTS.
        """
        node = self.nodes.get(current_node_id)
        if not node or not node.children_ids:
            return None
            
        # Get all children objects
        children = [self.nodes[mid] for mid in node.children_ids]
        
        # Sort by EFE (Lower is better)
        # We assume EFE is populated in score
        valid_children = [c for c in children if c.score]
        
        if not valid_children:
            return children[0] if children else None
            
        best_child = min(valid_children, key=lambda c: c.score.expected_free_energy)
        
        logger.info(f"Selected Branch: {best_child.id} (EFE: {best_child.score.expected_free_energy:.4f})")
        return best_child

    async def backtrack(self, current_node_id: str) -> Optional[ThoughtNode]:
        """
        Moves up the tree to the parent node.
        """
        node = self.nodes.get(current_node_id)
        if not node or not node.parent_id:
            return None
            
        parent = self.nodes.get(node.parent_id)
        logger.info(f"Backtracking from {current_node_id} to {parent.id}")
        return parent
