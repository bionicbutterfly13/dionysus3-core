from typing import Optional
from pydantic import BaseModel, Field

class BootstrapConfig(BaseModel):
    """Configuration for how recall is handled for a specific request."""
    enabled: bool = Field(default=True, description="Toggle for bootstrap recall")
    max_tokens: int = Field(default=2000, description="Hard limit for injected context")
    project_id: str = Field(..., description="Mandatory scoping ID")
    include_trajectories: bool = Field(default=True, description="Whether to fetch episodic history")

class BootstrapResult(BaseModel):
    """The output of the recall process injected into the agent."""
    formatted_context: str = Field(..., description="Markdown formatted string for injection")
    source_count: int = Field(..., description="Number of distinct memories found")
    summarized: bool = Field(default=False, description="Whether LLM summarization was triggered")
    latency_ms: float = Field(..., description="Total retrieval and formatting time")
