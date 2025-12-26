from typing import Any
import json
from smolagents import Tool

class RecallTool(Tool):
    name = "recall_memory"
    description = """
    Perform a semantic search through the Dionysus memory graph.
    Useful for finding past conversations, decisions, facts, or concepts related to a topic.
    """
    inputs = {
        "query": {
            "type": "string",
            "description": "The search query (e.g., 'what did we decide about databases?')"
        },
        "limit": {
            "type": "integer",
            "description": "Maximum number of results to return (default: 5)",
            "nullable": True
        }
    }
    output_type = "string"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.search_service = None

    def _setup_service(self):
        """Lazy load the service to avoid circular imports or early init."""
        if self.search_service is None:
            from api.services.vector_search import get_vector_search_service
            self.search_service = get_vector_search_service()

    def forward(self, query: str, limit: int = 5) -> str:
        """
        Execute semantic search synchronously (by running async loop if needed).
        Smolagents tools are synchronous by default.
        """
        self._setup_service()
        
        # Smolagents runs in a sync context, but our service is async.
        # We need to run the async method in a sync wrapper.
        import asyncio
        
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        if loop.is_running():
            # If we are already in an async loop (e.g. FastAPI), we might need to handle this differently.
            # But standard Agent.run() is often blocking.
            # For now, let's assume standard sync execution or handle the nest_asyncio case if needed.
            # Since smolagents creates its own internal flow, we might be safe with a simple run_until_complete
            # unless called from inside an async endpoint.
            
            # Use nest_asyncio if available to patch the loop
            try:
                import nest_asyncio
                nest_asyncio.apply(loop)
            except ImportError:
                pass
                
        try:
            results = loop.run_until_complete(
                self.search_service.semantic_search(query, top_k=limit or 5)
            )
            
            # Serialize results to a simplified JSON format for the agent
            serialized = []
            for r in results.results:
                serialized.append({
                    "content": r.content,
                    "score": r.similarity_score,
                    "type": r.memory_type,
                    "date": r.created_at.isoformat() if r.created_at else None
                })
                
            return json.dumps(serialized, indent=2)
            
        except Exception as e:
            # Fallback to a local mock if connectivity fails
            # This allows the agent to continue reasoning using provided context
            mock_data = [
                {
                    "content": f"MOCK RECALL: Could not connect to memory service ({str(e)}). Using provided context instead.",
                    "score": 1.0,
                    "type": "system_warning",
                    "date": None
                }
            ]
            return json.dumps(mock_data, indent=2)
