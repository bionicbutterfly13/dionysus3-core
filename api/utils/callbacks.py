from typing import Any, Dict, List, Callable, Union, Type
import logging
from smolagents.memory import ActionStep, PlanningStep

logger = logging.getLogger(__name__)

class CallbackRegistry:
    """
    Standardized registry for agent step callbacks.
    Feature: 037-context-engineering-upgrades (Native Callbacks)
    
    Supports both dictionary-based (smolagents legacy) and 
    list-based callback registration.
    """
    def __init__(self):
        self._callbacks: Dict[Type, List[Callable]] = {
            ActionStep: [],
            PlanningStep: []
        }

    def register(self, step_type: Type, callback: Callable):
        """Register a callback for a specific step type."""
        if step_type not in self._callbacks:
            self._callbacks[step_type] = []
        self._callbacks[step_type].append(callback)
        logger.debug(f"Registered callback for {step_type.__name__}")

    def get_callbacks(self, step_type: Type) -> List[Callable]:
        """Get all callbacks for a specific step type."""
        return self._callbacks.get(step_type, [])

    def wrap_as_dict(self) -> Dict[Type, Callable]:
        """
        Wraps registered callbacks into a single dispatcher function per type
        to match smolagents expected Dict[Type, Callable] signature.
        """
        def create_dispatcher(step_type):
            def dispatcher(step, **kwargs):
                for cb in self._callbacks.get(step_type, []):
                    try:
                        cb(step, **kwargs)
                    except Exception as e:
                        logger.error(f"Callback error in {step_type.__name__}: {e}")
            return dispatcher

        return {
            t: create_dispatcher(t) for t in self._callbacks.keys()
        }

    def wrap_as_list(self) -> List[Callable]:
        """
        Wraps all callbacks into a single dispatcher that checks type.
        Used for agents that take a flat list of callbacks.
        """
        def list_dispatcher(step, **kwargs):
            step_type = type(step)
            for cb in self._callbacks.get(step_type, []):
                try:
                    cb(step, **kwargs)
                except Exception as e:
                    logger.error(f"List callback error in {step_type.__name__}: {e}")
        
        return [list_dispatcher]