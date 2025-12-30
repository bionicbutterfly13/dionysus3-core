from typing import Callable, Type
from smolagents.memory import CallbackRegistry, MemoryStep

def get_callback_registry() -> CallbackRegistry:
    """Returns a new instance of CallbackRegistry."""
    return CallbackRegistry()

def register_callback(registry: CallbackRegistry, step_cls: Type[MemoryStep], callback: Callable):
    """Registers a callback for a specific step class."""
    registry.register(step_cls, callback)
