from smolagents import Tool
import asyncio
import json
from uuid import UUID

class ReviseModelTool(Tool):
    name = "revise_mental_model"
    description = """
    Revise a mental model's structure by adding or removing attractor basins.
    Use this when a model's predictions are inaccurate or when new information contradicts existing beliefs.
    """
    inputs = {
        "model_id": {
            "type": "string",
            "description": "UUID of the mental model to revise."
        },
        "trigger_description": {
            "type": "string",
            "description": "Description of why this revision is being made (e.g., 'Prediction error high')."
        },
        "add_basins": {
            "type": "string",
            "description": "JSON list of basin UUIDs to add.",
            "nullable": True
        },
        "remove_basins": {
            "type": "string",
            "description": "JSON list of basin UUIDs to remove.",
            "nullable": True
        }
    }
    output_type = "string"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.service = None

    def _setup_service(self):
        if self.service is None:
            from api.services.model_service import get_model_service
            # We assume the service is already initialized with a pool in the app context
            # If not, this might fail, but for the PoC/Agent context we rely on global singleton
            self.service = get_model_service()

    def forward(self, model_id: str, trigger_description: str, add_basins: str = None, remove_basins: str = None) -> str:
        """
        Execute model revision.
        """
        self._setup_service()
        
        from api.models.mental_model import ReviseModelRequest
        
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

        try:
            # Parse JSON inputs
            added = json.loads(add_basins) if add_basins else []
            removed = json.loads(remove_basins) if remove_basins else []
            
            request = ReviseModelRequest(
                trigger_description=trigger_description,
                add_basins=[UUID(b) for b in added],
                remove_basins=[UUID(b) for b in removed]
            )
            
            revision = loop.run_until_complete(
                self.service.apply_revision(UUID(model_id), request)
            )
            
            return json.dumps({
                "revision_id": str(revision.id),
                "model_id": str(revision.model_id),
                "accuracy_before": revision.accuracy_before,
                "accuracy_after": revision.accuracy_after,
                "message": "Model revision applied successfully"
            }, indent=2)
            
        except Exception as e:
            return f"Model revision failed: {str(e)}"
