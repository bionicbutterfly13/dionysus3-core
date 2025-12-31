"""
Dionysus Agent Tools Package

Class-based smolagents tools for cognitive operations.
"""

from api.agents.tools.cognitive_tools import (
    UnderstandQuestionTool,
    RecallRelatedTool,
    ExamineAnswerTool,
    BacktrackingTool,
    understand_question,
    recall_related,
    examine_answer,
    backtracking,
)

from api.agents.tools.kg_learning_tools import (
    AgenticKGExtractTool,
    agentic_kg_extract,
)

__all__ = [
    # Cognitive tools (D2-validated)
    "UnderstandQuestionTool",
    "RecallRelatedTool",
    "ExamineAnswerTool",
    "BacktrackingTool",
    "understand_question",
    "recall_related",
    "examine_answer",
    "backtracking",
    # KG Learning tools
    "AgenticKGExtractTool",
    "agentic_kg_extract",
]
