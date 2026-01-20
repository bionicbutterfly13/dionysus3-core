import asyncio
import logging
import uuid
import os
import json
from datetime import datetime
from typing import List, Dict, Any

from neo4j import GraphDatabase
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ingest_light")

load_dotenv()

# --- Configuration ---
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")

if not NEO4J_PASSWORD:
    raise ValueError("NEO4J_PASSWORD is required")

logger.info(f"Connecting to Neo4j at {NEO4J_URI}...")

class VigilantSentinelIngestor:
    def __init__(self):
        self.driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

    def close(self):
        self.driver.close()

    def create_trajectory(self, summary: str, trajectory_json: str, metadata: Dict) -> str:
        """Creates the Trajectory node (Source)."""
        ingest_id = str(uuid.uuid4())
        
        query = """
        CREATE (t:Trajectory {
            id: $id,
            summary: $summary,
            trajectory_type: 'structural',
            created_at: datetime(),
            metadata: $metadata,
            trajectory_json: $trajectory_json,
            project_id: $project_id,
            session_id: $session_id,
            source: 'manual_ingest'
        })
        RETURN t.id as id
        """
        
        with self.driver.session() as session:
            result = session.run(query, {
                "id": ingest_id,
                "summary": summary,
                "metadata": json.dumps(metadata),
                "trajectory_json": trajectory_json,
                "project_id": metadata.get("project_id"),
                "session_id": metadata.get("session_id")
            })
            return result.single()["id"]

    def ingest_relationships(self, source_id: str, relationships: List[Dict]):
        """Ingests entities and relationships linked to the source."""
        
        cypher_template = """
        MATCH (source {id: $source_id})
        
        MERGE (s:Entity {name: $source_name})
        ON CREATE SET s.id = randomUUID(), s.created_at = datetime(), s.type = $source_type, s.description = $source_desc
        ON MATCH SET s.type = $source_type, s.description = $source_desc

        MERGE (t:Entity {name: $target_name})
        ON CREATE SET t.id = randomUUID(), t.created_at = datetime(), t.type = $target_type, t.description = $target_desc
        ON MATCH SET t.type = $target_type, t.description = $target_desc
        
        MERGE (s)-[r:RELATED_TO {type: $rel_type}]->(t)
        SET r.evidence = $evidence, 
            r.confidence = $confidence,
            r.updated_at = datetime()
            
        MERGE (s)-[:MENTIONED_IN]->(source)
        MERGE (t)-[:MENTIONED_IN]->(source)
        """
        
        count = 0
        with self.driver.session() as session:
            for rel in relationships:
                # Dynamic Relationship Type trick: 
                # Neo4j python driver doesn't support dynamic type in parameter easily for MERGE without APOC.
                # But we can format the string carefully if we trust input.
                # However, to match `graphiti_service` EXACTLY, it uses :RELATED_TO {type: ...}
                # So we stick to that pattern which is safer and cleaner!
                
                # Check `graphiti_service.py` again...
                # It says: MERGE (s)-[r:RELATED_TO {type: row.relation_type}]->(t)
                # Yes, confirmed.
                
                session.run(cypher_template, {
                    "source_id": source_id,
                    "source_name": rel['source_name'],
                    "source_type": rel['source_type'],
                    "source_desc": rel['source_desc'],
                    
                    "target_name": rel['target_name'],
                    "target_type": rel['target_type'],
                    "target_desc": rel['target_desc'],
                    
                    "rel_type": rel['relation'],
                    "evidence": rel['evidence'],
                    "confidence": rel['confidence']
                })
                count += 1
                if count % 5 == 0:
                    logger.info(f"Ingested {count} relationships...")
        
        logger.info(f"Total relationships ingested: {count}")

def main():
    ingestor = VigilantSentinelIngestor()
    
    try:
        # DATA DEFINITION
        profile_name = "The Vigilant Sentinel"
        profile_desc = "High-functioning adults with ADHD, gifted/twice-exceptional minds. Hyper-analytical, emotionally hypersensitive."
        
        relationships = [
             # PAIN POINTS
            {
                "source_name": profile_name, "source_type": "AvatarArchetype", "source_desc": profile_desc,
                "target_name": "Pain: RSD (Rejection Sensitive Dysphoria)", "target_type": "PainPoint", 
                "target_desc": "Emotional volatility and rejection sensitivity. 'It hurts in my nervous system.'",
                "relation": "EXPERIENCES_PAIN", "evidence": "Not just sensitive — it hurts in my nervous system.", "confidence": 0.9
            },
            {
                "source_name": profile_name, "source_type": "AvatarArchetype", "source_desc": profile_desc,
                "target_name": "Pain: Executive Paralysis", "target_type": "PainPoint",
                "target_desc": "I know exactly what to do... I just can't make myself do it.",
                "relation": "EXPERIENCES_PAIN", "evidence": "It isn't willpower. My brain literally won't turn on.", "confidence": 0.9
            },
            {
                "source_name": profile_name, "source_type": "AvatarArchetype", "source_desc": profile_desc,
                "target_name": "Pain: Hollow Success Paradox", "target_type": "PainPoint",
                "target_desc": "External wins coupled with internal exhaustion.",
                "relation": "EXPERIENCES_PAIN", "evidence": "Why can I solve complex systems but can’t reply to an email?", "confidence": 0.8
            },
            {
                "source_name": profile_name, "source_type": "AvatarArchetype", "source_desc": profile_desc,
                "target_name": "Pain: Masking and Burnout", "target_type": "PainPoint",
                "target_desc": "Exhausting effort to appear normal.",
                "relation": "EXPERIENCES_PAIN", "evidence": "I’m a Hunter in a Farmer’s world.", "confidence": 0.85
            },
            
            # BELIEFS
            {
                "source_name": profile_name, "source_type": "AvatarArchetype", "source_desc": profile_desc,
                "target_name": "Belief: Hunter in Farmer's World", "target_type": "Belief",
                "target_desc": "Genius processing but incompatible with bureaucratic norms.",
                "relation": "HOLDS_BELIEF", "evidence": "Identity reflection", "confidence": 0.9
            },
            {
                "source_name": profile_name, "source_type": "AvatarArchetype", "source_desc": profile_desc,
                "target_name": "Belief: Productivity Systems Fail", "target_type": "Belief",
                "target_desc": "Conventional systems crumble under executive dysfunction.",
                "relation": "HOLDS_BELIEF", "evidence": "Lists and planners feel like punishment.", "confidence": 0.95
            },
            
            # DESIRES
            {
                "source_name": profile_name, "source_type": "AvatarArchetype", "source_desc": profile_desc,
                "target_name": "Desire: Psychological Traction", "target_type": "Desire",
                "target_desc": "Collapse inner-critic loops within minutes.",
                "relation": "DESIRES", "evidence": "Regain psychological traction immediately", "confidence": 1.0
            },
            {
                "source_name": profile_name, "source_type": "AvatarArchetype", "source_desc": profile_desc,
                "target_name": "Desire: Stop Paralysis", "target_type": "Desire",
                "target_desc": "Escape neuro-emotional paralysis reliably.",
                "relation": "DESIRES", "evidence": "Stop the freeze response", "confidence": 0.9
            },
            
            # FAILED SOLUTIONS
            {
                "source_name": profile_name, "source_type": "AvatarArchetype", "source_desc": profile_desc,
                "target_name": "Failed: Standard Planners/CBT", "target_type": "FailedSolution",
                "target_desc": "Frames struggle as ignorance/laziness vs neurological.",
                "relation": "REJECTS_SOLUTION", "evidence": "Lists and planners feel like punishment.", "confidence": 0.9
            }
        ]
        
        # EXECUTION
        logger.info("Creating Trajectory...")
        trajectory_id = ingestor.create_trajectory(
            summary="Manually ingested Vigilant Sentinel Avatar Profile via Lightweight Script",
            trajectory_json=json.dumps({"operation": "ingest_profile", "status": "manual"}),
            metadata={"project_id": "dionysus_core", "session_id": "avatar_ingest_light", "tags": ["avatar", "manual_ingest"]}
        )
        logger.info(f"Trajectory Created: {trajectory_id}")
        
        logger.info("Ingesting Relationships...")
        ingestor.ingest_relationships(trajectory_id, relationships)
        
        logger.info("Done!")

    finally:
        ingestor.close()

if __name__ == "__main__":
    main()
