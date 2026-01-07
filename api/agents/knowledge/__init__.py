"""
Knowledge Agents Module

Specialized smolagents for avatar research and knowledge extraction.
Feature: 019-avatar-knowledge-graph
"""

from api.agents.knowledge.pain_analyst import PainAnalyst
from api.agents.knowledge.objection_handler import ObjectionHandler
from api.agents.knowledge.voice_extractor import VoiceExtractor
from api.agents.knowledge.avatar_researcher import AvatarResearcher, create_avatar_researcher
from api.agents.tools.avatar_tools import (
    ingest_avatar_insight,
    query_avatar_graph,
    synthesize_avatar_profile,
    bulk_ingest_document,
)

__all__ = [
    # Agents
    "PainAnalyst",
    "ObjectionHandler",
    "VoiceExtractor",
    "AvatarResearcher",
    "create_avatar_researcher",
    # Tools
    "ingest_avatar_insight",
    "query_avatar_graph",
    "synthesize_avatar_profile",
    "bulk_ingest_document",
]
