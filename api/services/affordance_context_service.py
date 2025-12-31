"""
Affordance Context Service (Feature 048)
Models which actions/tools are 'afforded' by the current context.

Bridges the gap between raw tool availability and context-aware selection.
Reduces hallucinations by filtering out irrelevant tools.
"""

import logging
from typing import Dict, Any, List, Optional
from pydantic import BaseModel

from api.services.llm_service import chat_completion, GPT5_NANO

logger = logging.getLogger("dionysus.affordance")

class AffordanceMap(BaseModel):
    afforded_tools: List[str]
    rationale: str
    context_relevance: float

class AffordanceContextService:
    """
    Guides agent attention by modeling tool affordances.
    """
    
    def __init__(self):
        # Default affordances for common contexts
        self.default_affordances = {
            "mathematical": ["understand_question", "recall_related", "examine_answer", "backtracking"],
            "research": ["context_explorer", "recall_related", "graphiti_search"],
            "strategy": ["meta_tot_run", "identify_patterns", "reflect_on_topic"],
            "maintenance": ["maintenance_check", "consolidate_episodic_to_semantic"]
        }

    async def get_affordances(self, task: str, available_tools: List[str], context: Optional[Dict[str, Any]] = None) -> AffordanceMap:
        """
        Analyze task and context to determine which tools are 'afforded'.
        """
        context = context or {}
        
        prompt = f"""
        Analyze the following task and list of available tools.
        Identify which tools are most 'afforded' (logically useful and relevant) 
        given the specific nature of the problem.
        
        TASK: {task}
        AVAILABLE TOOLS: {', '.join(available_tools)}
        CONTEXT: {context.get('domain', 'general')}
        
        Respond with a JSON object:
        {{
            "afforded_tools": ["tool1", "tool2"],
            "rationale": "Why these tools are prioritized",
            "context_relevance": 0.9
        }}
        """
        
        try:
            response = await chat_completion(
                messages=[{"role": "user", "content": prompt}],
                system_prompt="You are an affordance modeling engine.",
                model=GPT5_NANO,
                max_tokens=256
            )
            
            # Simple parsing (using helper would be better but this is for the list)
            import json
            data = json.loads(response)
            return AffordanceMap(**data)
            
        except Exception as e:
            logger.error(f"Affordance calculation failed: {e}")
            # Fallback to defaults based on keywords
            task_lower = task.lower()
            matched_tools = []
            for domain, tools in self.default_affordances.items():
                if domain in task_lower:
                    matched_tools.extend(tools)
            
            # Intersect with actually available tools
            final_tools = list(set(matched_tools) & set(available_tools)) if matched_tools else available_tools[:5]
            
            return AffordanceMap(
                afforded_tools=final_tools,
                rationale="Fallback based on domain keywords.",
                context_relevance=0.5
            )

_affordance_instance: Optional[AffordanceContextService] = None

def get_affordance_service() -> AffordanceContextService:
    global _affordance_instance
    if _affordance_instance is None:
        _affordance_instance = AffordanceContextService()
    return _affordance_instance
