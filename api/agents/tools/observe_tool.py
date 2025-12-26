from smolagents import Tool
import asyncio
import json

class ObserveTool(Tool):
    name = "observe_environment"
    description = """
    Gather a snapshot of the current environment, including energy levels,
    heartbeat count, user presence, and counts of active goals and recent memories.
    Always use this at the start of a cycle to orient yourself.
    """
    inputs = {}
    output_type = "string"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.executor = None

    def _setup_service(self):
        if self.executor is None:
            from api.services.action_executor import get_action_executor
            self.executor = get_action_executor()

    def forward(self) -> str:
        """
        Execute observation and return environment snapshot.
        """
        self._setup_service()
        
        from api.models.action import ActionRequest
        from api.services.energy_service import ActionType
        
        import asyncio
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
        if loop.is_running():
            import nest_asyncio
            try:
                nest_asyncio.apply(loop)
            except ImportError:
                pass

        result = loop.run_until_complete(
            self.executor.execute(ActionRequest(action_type=ActionType.OBSERVE))
        )
        
        if result.success:
            return json.dumps(result.data.get("snapshot", {}), indent=2)
        else:
            return f"Observation failed: {result.error}"
