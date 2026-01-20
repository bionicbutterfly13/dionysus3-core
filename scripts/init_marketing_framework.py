import asyncio
import os
import logging
from pathlib import Path
from dotenv import load_dotenv
import sys

# Load environment variables
load_dotenv()

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from api.services.graphiti_service import get_graphiti_service, GraphitiConfig
from api.models.marketing import PDPArchitecture, FunnelStepType, EmotionalTriggerType

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("dionysus.init_marketing")

async def main():
    # Initialize Graphiti service
    config = GraphitiConfig(
        neo4j_uri=os.getenv("NEO4J_URI", "bolt://127.0.0.1:7687"),
        neo4j_password=os.getenv("NEO4J_PASSWORD"),
        openai_api_key=os.getenv("OPENAI_API_KEY")
    )
    graphiti_svc = await get_graphiti_service(config)

    # 1. Define the 15-Point SPIAD / RMBC2 PDP Architecture
    pdp_arch = PDPArchitecture(
        title="IAS 15-Point PDP Blueprint",
        sections=[
            {"id": "pre_headline", "purpose": "Self-selection / Qualifier", "trigger": "FEAR"},
            {"id": "question_headline", "purpose": "Curiosity gap", "trigger": "SEEKING"},
            {"id": "the_lead", "purpose": "Problem resonance / Agitate pain", "trigger": "PANIC_GRIEF"},
            {"id": "moht", "purpose": "Moment of Highest Tension (vivid pain)", "trigger": "FEAR"},
            {"id": "mohp", "purpose": "Moment of Highest Pleasure (future pacing)", "trigger": "LUST"},
            {"id": "slaughter_sacred_cows", "purpose": "Bust myths / Reframe", "trigger": "RAGE"},
            {"id": "blue_ocean_bridge", "purpose": "Introduce unique mechanism (UMS)", "trigger": "SEEKING"},
            {"id": "bio", "purpose": "Authority / Peer positioning", "trigger": "SOCIAL_PROOF"},
            {"id": "testimonials", "purpose": "Peer social proof", "trigger": "SOCIAL_PROOF"},
            {"id": "product_reveal", "purpose": "Transition to offer", "trigger": "LUST"},
            {"id": "product_tour", "purpose": "Module-by-module breakdown", "trigger": "SEEKING"},
            {"id": "golden_guarantee", "purpose": "Risk reversal", "trigger": "CARE"},
            {"id": "faq", "purpose": "Answer objections / Re-frame", "trigger": "SEEKING"},
            {"id": "perfect_for_you", "purpose": "Closing qualification", "trigger": "CARE"},
            {"id": "confident_appeal", "purpose": "Final CTA", "trigger": "SEEKING"}
        ]
    )

    # 2. Ingest Architecture as a "Ground Truth" Episode
    logger.info("Ingesting PDP Architecture into Graphiti...")
    await graphiti_svc.ingest_message(
        content=pdp_arch.model_dump_json(),
        source_description="pdp_architecture_blueprint",
        group_id="marketing-framework"
    )

    # 3. Ingest Macro-to-Micro Funnel Strategy
    macro_strategy = """
    FUNNEL FLOW: Cold Traffic → Advertorial → Opt-in → Lead Magnet (Replay Loop Breaker)
    → Lead Magnet Delivery (5 emails) → Email Sequence (1-20) → VSL → $97 Tripwire
    
    UMP: The Split Self Architecture (Energy drain from maintaining two identities)
    UMS: Predictive Identity Recalibration (Updating threat predictions via Memory Reconsolidation)
    """
    
    logger.info("Ingesting Macro Funnel Strategy...")
    await graphiti_svc.ingest_message(
        content=macro_strategy,
        source_description="macro_funnel_strategy",
        group_id="marketing-framework"
    )

    await graphiti_svc.close()
    logger.info("Marketing Framework Initialization Complete.")

if __name__ == "__main__":
    asyncio.run(main())
