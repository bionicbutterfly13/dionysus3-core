"""
MCP Tools for Cognitive Functions (Feature 042)
Wraps the internal smolagents tools for external MCP access.
"""
import asyncio
from typing import Optional, Dict, Any
from api.agents.tools.cognitive_tools import (
    understand_question,
    recall_related,
    examine_answer,
    backtracking
)

async def _run_tool_in_thread(tool_func, *args, **kwargs) -> Dict[str, Any]:
    """Run a blocking tool method in a separate thread to avoid blocking the MCP loop."""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, lambda: tool_func(*args, **kwargs))

async def cognitive_understand_tool(question: str, context: Optional[str] = None) -> dict:
    """
    Decompose a complex problem using the UnderstandQuestion tool.
    """
    return await _run_tool_in_thread(understand_question.forward, question=question, context=context)

async def cognitive_recall_tool(question: str, context: Optional[str] = None) -> dict:
    """
    Retrieve analogous examples using the RecallRelated tool.
    """
    return await _run_tool_in_thread(recall_related.forward, question=question, context=context)

async def cognitive_examine_tool(question: str, current_reasoning: str, context: Optional[str] = None) -> dict:
    """
    Critique and verify reasoning using the ExamineAnswer tool.
    """
    return await _run_tool_in_thread(examine_answer.forward, question=question, current_reasoning=current_reasoning, context=context)

async def cognitive_backtrack_tool(question: str, current_reasoning: str, context: Optional[str] = None) -> dict:
    """
    Propose alternative strategies using the Backtracking tool.
    """
    return await _run_tool_in_thread(backtracking.forward, question=question, current_reasoning=current_reasoning, context=context)
