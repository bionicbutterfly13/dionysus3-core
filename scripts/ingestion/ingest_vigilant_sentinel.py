import asyncio
import logging
import uuid
import os
from datetime import datetime
from typing import List, Dict, Any

from dotenv import load_dotenv

from api.models.avatar import (
    AvatarProfile, 
    PainPoint, 
    Objection, 
    Desire, 
    Belief, 
    Behavior, 
    FailedSolution, 
    VoicePattern
)
from api.models.memevolve import (
    MemoryIngestRequest, 
    TrajectoryData, 
    TrajectoryStep, 
    TrajectoryMetadata, 
    TrajectoryType
)
from api.services.memevolve_adapter import get_memevolve_adapter

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ingest_vigilant_sentinel")

def create_vigilant_sentinel_profile() -> AvatarProfile:
    """
    Construct the Vigilant Sentinel avatar profile from user data.
    """
    profile = AvatarProfile(
        name="The Vigilant Sentinel",
        demographics={
            "description": "High-functioning adults with ADHD, gifted/twice-exceptional minds, and empathic or HSP tendencies",
            "psychographics": "Hyper-analytical, emotionally hypersensitive, spiritually curious, intellectually driven, system-suspicious"
        },
        pain_points=[
            PainPoint(
                description="Emotional volatility and Rejection Sensitivity Dysphoria (RSD)",
                category="emotional",
                intensity=0.9,
                expressed_as="Unbearable emotional pain that derails focus",
                source_quote="Not just sensitive — it hurts in my nervous system."
            ),
            PainPoint(
                description="Executive dysfunction and task paralysis",
                category="functional",
                intensity=0.9,
                trigger="Perceived enormity of tasks or lack of dopamine",
                expressed_as="I know exactly what to do... I just can't make myself do it.",
                source_quote="It isn't willpower. My brain literally won't turn on until something is urgent."
            ),
            PainPoint(
                description="Hollow Success Paradox",
                category="achievement",
                intensity=0.8,
                expressed_as="External wins coupled with internal exhaustion",
                source_quote="Why can I solve complex systems but can’t reply to an email?"
            ),
            PainPoint(
                description="Masking and Burnout",
                category="identity",
                intensity=0.85,
                expressed_as="Exhausting effort to appear normal",
                source_quote="I’m a Hunter in a Farmer’s world."
            )
        ],
        beliefs=[
            Belief(
                content="I'm a Hunter in a Farmer's world - genius processing but incompatible with bureaucratic norms",
                certainty=0.9,
                origin="Identity reflection",
                limiting=False # It's a reframe, but can be limiting if used as an excuse, here it's identity
            ),
            Belief(
                content="Conventional productivity systems crumble the moment real executive dysfunction shows up",
                certainty=0.95,
                limiting=True,
                blocks=["Adoption of standard tools"]
            ),
            Belief(
                content="I am broken because I can't do simple things despite my intellect",
                certainty=0.8,
                limiting=True,
                blocks=["Self-trust"]
            )
        ],
        desires=[
            Desire(
                description="Collapse inner-critic loops and emotional spirals within minutes",
                priority=10,
                expressed_as="Regain psychological traction immediately"
            ),
            Desire(
                description="Escape neuro-emotional paralysis reliably",
                priority=9,
                expressed_as="Stop the freeze response"
            ),
            Desire(
                description="Rebuild trust in their own inner system",
                priority=8,
                expressed_as="Trust myself to execute"
            )
        ],
        failed_solutions=[
            FailedSolution(
                name="Standard Planners/CBT",
                category="self-help",
                why_failed="Frames struggle as ignorance/laziness vs neurological",
                residual_belief="Lists and planners feel like punishment, not help."
            )
        ],
        voice_patterns=[
            VoicePattern(phrase="I know exactly what to do… I just can’t make myself do it.", emotional_tone="frustrated"),
            VoicePattern(phrase="It’s not procrastination or laziness — I know I need to start, but my body refuses.", emotional_tone="desperate"),
            VoicePattern(phrase="It hurts in my nervous system.", emotional_tone="painful")
        ]
    )
    return profile

def convert_profile_to_graph_elements(profile: AvatarProfile) -> tuple[List[Dict], List[Dict]]:
    """
    Convert AvatarProfile to nodes and edges for Graphiti ingestion.
    """
    entities = []
    relationships = []
    
    # 1. Main Avatar Entity
    avatar_id = "avatar_vigilant_sentinel"
    entities.append({
        "name": profile.name,
        "type": "AvatarArchetype",
        "description": profile.demographics.get("description", "")
    })
    
    # 2. Pain Points
    for i, pp in enumerate(profile.pain_points):
        pp_name = f"Pain: {pp.description[:50]}..."
        entities.append({
            "name": pp_name,
            "type": "PainPoint",
            "description": pp.expressed_as or pp.description
        })
        relationships.append({
            "source": profile.name,
            "target": pp_name,
            "relation": "EXPERIENCES_PAIN",
            "evidence": pp.source_quote or pp.description,
            "confidence": pp.intensity
        })
        
    # 3. Beliefs
    for belief in profile.beliefs:
        b_name = f"Belief: {belief.content[:50]}..."
        entities.append({
            "name": b_name,
            "type": "Belief",
            "description": belief.content
        })
        relationships.append({
            "source": profile.name,
            "target": b_name,
            "relation": "HOLDS_BELIEF",
            "evidence": belief.content,
            "confidence": belief.certainty
        })
        
    # 4. Desires
    for desire in profile.desires:
        d_name = f"Desire: {desire.description[:50]}..."
        entities.append({
            "name": d_name,
            "type": "Desire",
            "description": desire.description
        })
        relationships.append({
            "source": profile.name,
            "target": d_name,
            "relation": "DESIRES",
            "evidence": desire.expressed_as,
            "confidence": 1.0
        })

    # 5. Failed Solutions
    for sol in profile.failed_solutions:
        s_name = f"Failed: {sol.name}"
        entities.append({
            "name": s_name,
            "type": "FailedSolution",
            "description": sol.why_failed
        })
        relationships.append({
            "source": profile.name,
            "target": s_name,
            "relation": "REJECTS_SOLUTION",
            "evidence": sol.residual_belief,
            "confidence": 0.9
        })
        
    return entities, relationships

async def main():
    logger.info("Initializing MemEvolve Adapter...")
    adapter = get_memevolve_adapter()
    
    logger.info("Constructing Vigilant Sentinel Profile...")
    profile = create_vigilant_sentinel_profile()
    
    logger.info("Converting to Graph Elements...")
    entities, edges = convert_profile_to_graph_elements(profile)
    
    # Construct TrajectoryData wrapper
    trajectory = TrajectoryData(
        query="Ingest Vigilant Sentinel Avatar Profile",
        summary=f"Ingestion of the 'Vigilant Sentinel' avatar profile: {profile.demographics['description']}",
        steps=[
            TrajectoryStep(
                observation="User provided deep psychographic profile",
                action="Structurize into AvatarProfile model",
                thought="Persisting as rigorous semantic memory in Graphiti"
            )
        ],
        metadata=TrajectoryMetadata(
            project_id="dionysus_core",
            session_id="avatar_ingestion_001",
            timestamp=datetime.utcnow(),
            tags=["avatar", "marketing", "psychographics", "vigilant_sentinel"],
            trajectory_type=TrajectoryType.STRUCTURAL
        )
    )
    
    request = MemoryIngestRequest(
        trajectory=trajectory,
        entities=entities,
        edges=edges,
        project_id="dionysus_core",
        session_id="avatar_ingestion_001",
        memory_type="semantic"
    )
    
    logger.info(f"Ingesting {len(entities)} entities and {len(edges)} relationships via MemEvolve...")
    result = await adapter.ingest_trajectory(request)
    
    logger.info(f"Ingestion Complete! Result: {result}")

if __name__ == "__main__":
    asyncio.run(main())
