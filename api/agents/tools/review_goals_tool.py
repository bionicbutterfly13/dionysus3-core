from smolagents import Tool
import asyncio
import json

class ReviewGoalsTool(Tool):
    name = "review_goals"
    description = """
    Review the current state of all goals (active, queued, backlog).
    Returns an assessment including blocked goals, stale goals, and suggestions.
    Use this to decide which goals to focus on or reprioritize.
    """
    inputs = {}
    output_type = "string"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.service = None

    def _setup_service(self):
        if self.service is None:
            from api.services.goal_service import get_goal_service
            self.service = get_goal_service()

    def forward(self) -> str:
        """
        Execute goal review.
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

        assessment = loop.run_until_complete(self.service.review_goals())
        
        # Serialize assessment manually to ensure clean JSON
        return json.dumps({
            "active_goals": [{"id": str(g.id), "title": g.title, "priority": g.priority.value} for g in assessment.active_goals],
            "queued_goals": [{"id": str(g.id), "title": g.title} for g in assessment.queued_goals],
            "blocked_goals": [{"id": str(g.id), "title": g.title, "blocked_by": g.blocked_by.description if g.blocked_by else "unknown"} for g in assessment.blocked_goals],
            "issues": assessment.issues,
            "needs_brainstorm": assessment.needs_brainstorm
        }, indent=2)
