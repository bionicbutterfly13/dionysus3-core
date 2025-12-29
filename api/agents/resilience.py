"""
Resilience & Self-Healing Service
Feature: 034-self-healing-resilience

Provides agents with 'Plan B' strategies when tools or processes fail.
"""

import logging
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)

# Registry of common failures and their 'Plan B' counterparts
RECOVERY_STRATEGIES = {
    "TIMEOUT": {
        "hint": "The previous attempt timed out. Try a more specific, smaller task or use a simpler tool.",
        "action_adjustment": "REDUCE_SCOPE"
    },
    "EMPTY_SEARCH": {
        "hint": "No results found. Try broadening your search terms or use 'query_wisdom_graph' for conceptual context.",
        "action_adjustment": "BROADEN_QUERY"
    },
    "PARSING_ERROR": {
        "hint": "The output format was invalid. Try re-running with an explicit request for JSON and simple language.",
        "action_adjustment": "SIMPLIFY_FORMAT"
    },
    "BRIDGE_FAILURE": {
        "hint": "The MCP Tool Bridge is currently unstable. Fall back to internal reasoning or local reflection tools.",
        "action_adjustment": "LOCAL_ONLY"
    }
}

class StrategyHinter:
    """
    Analyzes error messages and generates 'Plan B' suggestions for agents.
    """
    @staticmethod
    def get_hint(error_msg: str) -> str:
        error_msg = error_msg.upper()
        
        if "TIMEOUT" in error_msg:
            strategy = RECOVERY_STRATEGIES["TIMEOUT"]
        elif "EMPTY" in error_msg or "NO RESULTS" in error_msg:
            strategy = RECOVERY_STRATEGIES["EMPTY_SEARCH"]
        elif "JSON" in error_msg or "PARSE" in error_msg or "FORMAT" in error_msg:
            strategy = RECOVERY_STRATEGIES["PARSING_ERROR"]
        elif "BRIDGE" in error_msg or "MCP" in error_msg:
            strategy = RECOVERY_STRATEGIES["BRIDGE_FAILURE"]
        else:
            return f"Error encountered: {error_msg}. Please try an alternative approach."
            
        return f"RECOVERY_HINT: {strategy['hint']} Strategy: {strategy['action_adjustment']}"

def wrap_with_resilience(observation: Any) -> Any:
    """
    Hijacks tool observations to inject recovery hints if an error is detected.
    """
    obs_str = str(observation)
    if "Error" in obs_str or "failed" in obs_str.lower() or "timeout" in obs_str.lower():
        hint = StrategyHinter.get_hint(obs_str)
        return f"{obs_str}\n\n{hint}"
    return observation
