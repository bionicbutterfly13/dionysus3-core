import logging
import time
import asyncio
from typing import List, Optional, Dict, Any
from api.models.bootstrap import BootstrapConfig, BootstrapResult
from api.services.vector_search import get_vector_search_service, SearchFilters
from api.services.graphiti_service import get_graphiti_service
from api.services.llm_service import chat_completion, GPT5_NANO

class BootstrapRecallService:
    """
    Service for automated agent session grounding via hybrid recall.
    """
    def __init__(self):
        self.logger = logging.getLogger("dionysus.bootstrap_recall")
        self._current_trace_id: Optional[str] = None

    @property
    def trace_id(self) -> str:
        return self._current_trace_id or "no-trace"

    @trace_id.setter
    def trace_id(self, value: str):
        self._current_trace_id = value

    def _log(self, level: int, event: str, **kwargs):
        extra = kwargs
        extra["trace_id"] = self.trace_id
        self.logger.log(level, event, extra=extra)

    async def recall_context(self, query: str, project_id: str, config: Optional[BootstrapConfig] = None) -> BootstrapResult:
        """
        Primary entry point for bootstrap recall.
        """
        start_time = time.time()
        self._log(logging.INFO, "bootstrap_recall_started", query=query, project_id=project_id)
        
        if config is None:
            config = BootstrapConfig(project_id=project_id)

        try:
            # Execute hybrid retrieval with timeout
            # We use wait_for to enforce the 5s spec requirement (increased from 2s)
            result = await asyncio.wait_for(
                self._execute_recall(query, project_id, config),
                timeout=5.0
            )
        except asyncio.TimeoutError:
            self._log(logging.WARNING, "bootstrap_recall_timeout")
            result = BootstrapResult(
                formatted_context="## Past Context\n*Recall timed out.*",
                source_count=0,
                summarized=False,
                latency_ms=(time.time() - start_time) * 1000
            )
        except Exception as e:
            self._log(logging.ERROR, "bootstrap_recall_failed", error=str(e))
            result = BootstrapResult(
                formatted_context="## Past Context\n*Recall failed due to internal error.*",
                source_count=0,
                summarized=False,
                latency_ms=(time.time() - start_time) * 1000
            )
        
        self._log(logging.INFO, "bootstrap_recall_completed", latency_ms=result.latency_ms)
        return result

    async def _execute_recall(self, query: str, project_id: str, config: BootstrapConfig) -> BootstrapResult:
        start_time = time.time()
        
        # 1. Fetch semantic memories
        semantic_memories = await self._fetch_semantic_memories(query, project_id)
        
        # 2. Fetch temporal trajectories
        trajectories = []
        if config.include_trajectories:
            trajectories = await self._fetch_temporal_trajectories(project_id)
            
        # 3. Format block
        full_context = self._format_markdown_block(semantic_memories, trajectories, project_id)
        
        # 4. Summarize and Truncate to Budget (T015)
        source_count = len(semantic_memories) + len(trajectories)
        summarized = False
        
        # Check token count properly
        token_count = self._get_token_count(full_context)
        if token_count > config.max_tokens:
            full_context = await self._summarize_if_needed(full_context)
            summarized = True
            
        # Final safety truncation
        full_context = self._truncate_to_budget(full_context, config.max_tokens)
            
        return BootstrapResult(
            formatted_context=full_context,
            source_count=source_count,
            summarized=summarized,
            latency_ms=(time.time() - start_time) * 1000
        )

    def _get_token_count(self, text: str) -> int:
        """Calculate token count using tiktoken."""
        import tiktoken
        try:
            encoding = tiktoken.encoding_for_model("gpt-4o") # Close enough for gpt-5
            return len(encoding.encode(text))
        except Exception:
            return len(text) // 4 # Fallback

    def _truncate_to_budget(self, text: str, max_tokens: int) -> str:
        """Hard truncation to ensure budget compliance (T015)."""
        import tiktoken
        try:
            encoding = tiktoken.encoding_for_model("gpt-4o")
            tokens = encoding.encode(text)
            if len(tokens) <= max_tokens:
                return text
            
            truncated = encoding.decode(tokens[:max_tokens])
            return truncated + "\n\n*...[Context truncated to fit token budget]*"
        except Exception:
            # Char-based fallback: ~4 chars per token
            limit = max_tokens * 4
            if len(text) <= limit:
                return text
            return text[:limit] + "\n\n*...[Context truncated]*"

    async def _fetch_semantic_memories(self, query: str, project_id: str) -> List[Dict[str, Any]]:
        vector_svc = get_vector_search_service()
        filters = SearchFilters(project_id=project_id)
        response = await vector_svc.semantic_search(query=query, top_k=5, filters=filters)
        return [{"content": r.content, "score": r.similarity_score, "type": r.memory_type} for r in response.results]

    async def _fetch_temporal_trajectories(self, project_id: str) -> List[Dict[str, Any]]:
        graphiti = await get_graphiti_service()
        # Search for recent episodes/trajectories
        # In this architecture, we use semantic search with a generic "recent" query or specialized temporal fetch
        # For bootstrap, we'll look for recent trajectories
        results = await graphiti.search(f"Latest task trajectories for project {project_id}", top_k=3)
        return [{"content": r['content'], "type": "trajectory"} for r in results]

    def _format_markdown_block(self, semantic: List[Dict], temporal: List[Dict], project_id: str) -> str:
        lines = [f"## Past Context (Project: {project_id})", ""]
        
        if temporal:
            lines.append("### Recent Trajectories")
            for t in temporal:
                lines.append(f"- {t['content']}")
            lines.append("")
            
        if semantic:
            lines.append("### Relevant Semantic Memories")
            for s in semantic:
                lines.append(f"- {s['content']} (relevance: {s['score']:.2f})")
            lines.append("")
            
        if not semantic and not temporal:
            lines.append("*No relevant past context found.*")
            
        return "\n".join(lines)

    async def _summarize_if_needed(self, context: str) -> str:
        self._log(logging.INFO, "summarizing_context", original_length=len(context))
        
        prompt = f"""Summarize the following project context for an AI agent. 
Preserve all specific identifiers, feature names, and current status.
Keep the summary concise and focused on grounding the agent for a new task.

Context:
{context}
"""
        summary = await chat_completion(
            messages=[{"role": "user", "content": prompt}],
            model=GPT5_NANO
        )
        return f"## Past Context (Summarized)\n\n{summary}"
