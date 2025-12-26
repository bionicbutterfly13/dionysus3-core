from smolagents import Tool
import asyncio
import json

class UpdateEnergyTool(Tool):
    name = "manage_energy"
    description = """
    Check current energy levels or deduct energy after performing an action.
    Dionysus operates on a finite energy budget.
    """
    inputs = {
        "operation": {
            "type": "string",
            "description": "The operation to perform: 'get_status' or 'spend_energy'."
        },
        "amount": {
            "type": "number",
            "description": "Amount of energy to spend (required if operation is 'spend_energy').",
            "nullable": True
        }
    }
    output_type = "string"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.energy_service = None

    def _setup_service(self):
        if self.energy_service is None:
            from api.services.energy_service import get_energy_service
            self.energy_service = get_energy_service()

    def forward(self, operation: str, amount: float = 0.0) -> str:
        """
        Execute energy management operations.
        """
        self._setup_service()
        
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

        if operation == "get_status":
            state = loop.run_until_complete(self.energy_service.get_state())
            return json.dumps({
                "current_energy": state.current_energy,
                "heartbeat_count": state.heartbeat_count,
                "paused": state.paused
            })
        elif operation == "spend_energy":
            success, remaining = loop.run_until_complete(self.energy_service.spend_energy(amount or 0.0))
            return json.dumps({
                "success": success,
                "remaining_energy": remaining,
                "message": "Energy spent successfully" if success else "Insufficient energy"
            })
        else:
            return f"Unknown operation: {operation}"
