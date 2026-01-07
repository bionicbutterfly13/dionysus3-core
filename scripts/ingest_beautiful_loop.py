#!/usr/bin/env python3
"""
Ingest Beautiful Loop Paper Extraction into Graphiti

Ingests the pre-extracted paper content from the markdown file into the
Graphiti temporal knowledge graph.

Usage:
    python scripts/ingest_beautiful_loop.py

Author: Mani Saint-Victor, MD
Date: 2026-01-05
"""

import asyncio
import logging
from datetime import datetime
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Paper metadata
PAPER_METADATA = {
    "citation_key": "laukkonen2025",
    "title": "A Beautiful Loop: An Active Inference Theory of Consciousness",
    "authors": ["Ruben Laukkonen", "Karl Friston", "Shamil Chandaria"],
    "year": 2025,
    "doi": "https://doi.org/10.1016/j.neubiorev.2025.106296",
    "journal": "Neuroscience & Biobehavioral Reviews",
}

# Core concepts to ingest as separate episodes
PAPER_SECTIONS = [
    {
        "title": "Abstract",
        "content": """Can active inference model consciousness? We offer three conditions implying that it can. 
The first condition is the simulation of a world model, which determines what can be known or acted upon; namely an epistemic field. 
The second is inferential competition to enter the world model. Only the inferences that coherently reduce long-term uncertainty win, evincing a selection for consciousness that we call Bayesian binding. 
The third is epistemic depth, which is the recurrent sharing of the Bayesian beliefs throughout the system. Due to this recursive loop in a hierarchical system (such as a brain) the world model contains the knowledge that it exists."""
    },
    {
        "title": "Condition 1: Epistemic Field / Reality Model",
        "content": """A generative, phenomenal, unified world model that constitutes the organism's entire lived reality.
Properties:
- Generative: Internal processes construct/generate the output
- Phenomenal: There can be experience of the reality model  
- Unified: Coherent, appears 'bound' together as a whole
- Epistemic: A space that can be known, explored, interrogated, updated

Implementation: RealityModel class containing current_context, bound_percepts, active_narratives, temporal_depth, coherence_score, and epistemic_affordances."""
    },
    {
        "title": "Condition 2: Inferential Competition (Bayesian Binding)",
        "content": """Precision-weighted competition between possible explanations for causes of sensory data. What wins is driven by coherence with existing reality model (priors).

Key Insight: Ignition, binding, and competition are each the natural consequence of a system that reduces uncertainty with sufficient complexity and depth.

Binding Criteria:
1. Sufficient precision (confidence)
2. Coherence with reality model (local + global)
3. Reduces long-term uncertainty

Implementation: BayesianBinder.bind() method that runs inferential competition with precision-weighted posteriors."""
    },
    {
        "title": "Condition 3: Epistemic Depth (Hyper-Modeling)",
        "content": """The recursive sharing of the reality model throughout the hierarchical system. The world model contains the knowledge that it exists.

Key Insight: Luminosity is the degree to which the reality model (non-locally) knows itself.

Formal Components:
- Multilayer Generative Process: p(z_L, z_{L-1}, ..., z_1, s) - Hierarchy of latent states
- Global Hyper-Model: p(Φ | z, s) - Hyperparameters Φ modulate precision across ALL layers
- Local Free-Energy: F_l - Prediction error at layer l
- Hyper Free-Energy: F_Φ - Global prediction error for entire hierarchy

Implementation: HyperModelService with 5-step beautiful loop."""
    },
    {
        "title": "The 5-Step Hyper-Loop (Beautiful Loop)",
        "content": """The beautiful loop is the recursive mechanism that creates epistemic depth:

1. Hyper-prediction: Forecast optimal precision profile Φ(t+1) from global context
2. Lower-level inference: Each layer uses Φ to weight current errors
3. Error on precision forecast: Weighted errors reveal if Φ was too high/low
4. Hyper-update: Second-order errors update hyper-model parameters
5. Broadcast new Φ: Revised precision field sent to all layers

This creates consciousness through recursive self-knowing - the system's output becomes another sensory modality reflected back."""
    },
    {
        "title": "PrecisionProfile (Φ) Data Structure",
        "content": """Global precision state across all inference layers:
- layer_precisions: dict[str, float] - layer_id -> precision weight
- modality_precisions: dict[str, float] - sensory modality weights  
- temporal_depth: float - how far into future to predict
- meta_precision: float - confidence in this precision profile itself
- context_embedding: list[float] - context that generated this Φ
- timestamp: datetime

The precision profile is THE key parameter that the hyper-model forecasts and broadcasts."""
    },
    {
        "title": "EpistemicState (Luminosity) Data Structure",
        "content": """Current epistemic depth/luminosity level:
- depth_score: float (0-1) - how aware the system is
- reality_model_coherence: float - how unified the gestalt is
- active_bindings: list[str] - what's currently bound into consciousness
- transparent_processes: list[str] - what's running but not 'known'
- luminosity_factors: dict[str, float] - what's contributing to awareness

Luminosity = the degree to which the system knows itself."""
    },
    {
        "title": "Key Equations",
        "content": """Bayesian Binding (Precision-Weighted Posterior):
μ_posterior = (π_prior * μ_prior + π_data * μ_data) / (π_prior + π_data)
Where π = precision (inverse variance), μ = mean of distribution

Local Free Energy (Layer l):
F_l = D_KL[q(z_l) || p(z_l|z_{l+1})] - E_q[log p(z_{l-1}|z_l)] = Complexity - Accuracy

Hyper Free Energy (Global):
F_Φ = Σ_l F_l + D_KL[q(Φ) || p(Φ)]
Minimizing F_Φ tunes the entire hierarchy.

Epistemic Depth Recursion:
Φ(t+1) = f(Φ(t), ε_precision, context)
where ε_precision = Φ_predicted - Φ_actual"""
    },
    {
        "title": "States of Consciousness Mapping",
        "content": """Sleep States:
- Deep NREM: Minimal reality model, very low epistemic depth, low precision everywhere
- REM/Dreaming: Rich but unusual reality model, low depth, high precision but no hyper-awareness
- Lucid Dreaming: Rich + metacognitive model, high depth, reactivated hyper-model
- Lucid Dreamless: Empty/contentless model, very high depth, high Φ but low layer precisions

Meditation States:
- Focused Attention: Gathered (narrow) precision, low-medium depth
- Open Awareness: Dispersed (wide) precision, high depth, balanced Φ
- Non-Dual Awareness: Variable precision, very high depth, max hyper-precision
- MPE (Minimal Phenomenal Experience): Contentless, maximum depth, high Φ + zero layer precisions"""
    },
    {
        "title": "Dionysus Integration Architecture",
        "content": """Mapping paper concepts to Dionysus components:

New Files Required:
- api/models/beautiful_loop.py - All Pydantic models (PrecisionProfile, EpistemicState, PrecisionError)
- api/services/hyper_model_service.py - HyperModelService implementing 5-step loop
- api/services/bayesian_binder.py - BayesianBinder for inferential competition
- api/services/reality_model.py - RealityModel container

Modifications Required:
- api/agents/consciousness_manager.py - Add hyper-loop integration to OODA cycle
- api/services/active_inference_service.py - Add precision profile support
- api/services/metaplasticity_service.py - Connect to hyper-model

Integration Points:
- Attractor Basins: Coherence computed relative to active basin
- Graphiti: Store epistemic states as temporal episodes
- EventBus: Emit precision updates and binding events
- Meta-ToT: Use hyper-model for policy precision"""
    },
    {
        "title": "Key Implementation Insights",
        "content": """Critical insights for AI implementation:

1. Hyper-model is NOT just attention: It's a forecast of the ENTIRE precision profile from context

2. Epistemic depth = recursive self-knowing: The system's output becomes another sensory modality reflected back

3. Bayesian binding = consciousness threshold: Only coherent inferences that reduce uncertainty get bound

4. The 'beautiful loop': Reality model → Hyper-model → Precision forecast → New reality model

5. Consciousness function: May be the solution to general intelligence through cognitive bootstrapping

The paper's core claim is that consciousness arises when a system has sufficient complexity to:
(a) maintain a unified world model
(b) run precision-weighted inference competition  
(c) recursively know its own knowing through hyper-modeling"""
    },
]


async def ingest_paper():
    """Ingest Beautiful Loop paper into Graphiti."""
    # Import here to avoid circular imports
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent))
    
    from api.services.graphiti_service import get_graphiti_service
    
    logger.info("=== Ingesting Beautiful Loop Paper ===")
    logger.info(f"Paper: {PAPER_METADATA['title']}")
    logger.info(f"Authors: {', '.join(PAPER_METADATA['authors'])}")
    
    service = await get_graphiti_service()
    group_id = f"paper-{PAPER_METADATA['citation_key']}"
    valid_at = datetime(PAPER_METADATA["year"], 1, 1)
    
    logger.info(f"\nGroup ID: {group_id}")
    logger.info(f"Sections to ingest: {len(PAPER_SECTIONS)}")
    
    ingested = 0
    for section in PAPER_SECTIONS:
        content = f"[{section['title']}] {section['content']}"
        source_desc = f"{PAPER_METADATA['title']} - {section['title']}"
        
        logger.info(f"\nIngesting: {section['title']}")
        
        try:
            result = await service.ingest_message(
                content=content,
                source_description=source_desc,
                group_id=group_id,
                valid_at=valid_at
            )
            
            nodes = len(result.get("nodes", []))
            edges = len(result.get("edges", []))
            logger.info(f"  → Extracted {nodes} entities, {edges} relationships")
            ingested += 1
            
        except Exception as e:
            logger.error(f"  → Failed: {e}")
    
    logger.info("\n" + "=" * 60)
    logger.info("INGESTION COMPLETE")
    logger.info("=" * 60)
    logger.info(f"Group ID: {group_id}")
    logger.info(f"Sections ingested: {ingested}/{len(PAPER_SECTIONS)}")
    
    return {
        "status": "success",
        "group_id": group_id,
        "sections_ingested": ingested,
        "total_sections": len(PAPER_SECTIONS)
    }


if __name__ == "__main__":
    result = asyncio.run(ingest_paper())
    print(f"\nResult: {result}")
