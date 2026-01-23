#!/usr/bin/env python3
"""
Quick test script for Graphiti integration.
Run: python scripts/test_graphiti.py
"""

import asyncio
import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv(override=True)

from api.services.graphiti_service import GraphitiService, GraphitiConfig


async def main():
    print("=" * 60)
    print("Graphiti Integration Test")
    print("=" * 60)

    # Check env vars
    neo4j_uri = os.getenv("NEO4J_URI", "bolt://72.61.78.89:7687")
    print(f"\nNeo4j URI: {neo4j_uri}")
    print(f"OpenAI API Key: {'✓ set' if os.getenv('OPENAI_API_KEY') else '✗ missing'}")
    print(f"Neo4j Password: {'✓ set' if os.getenv('NEO4J_PASSWORD') else '✗ missing'}")

    if not os.getenv("OPENAI_API_KEY") or not os.getenv("NEO4J_PASSWORD"):
        print("\n❌ Missing required environment variables")
        return

    try:
        # Initialize
        print("\n1. Initializing Graphiti...")
        config = GraphitiConfig(group_id="graphiti_test")
        service = GraphitiService(config)
        await service.initialize()
        print("   ✓ Initialized")

        # Health check
        print("\n2. Health check...")
        health = await service.health_check()
        print(f"   Health: {health}")

        # Ingest test message
        print("\n3. Ingesting test message...")
        test_message = """
        Dr. Mani Saint-Victor is working on Dionysus, an AI consciousness system.
        The project uses Neo4j for graph storage and PostgreSQL for working memory.
        Today is December 2024 and the team is integrating Graphiti for real-time entity tracking.
        """
        result = await service.ingest_message(
            content=test_message,
            source_description="test script",
        )
        print(f"   Episode: {result.get('episode_uuid')}")
        print(f"   Extracted {len(result.get('nodes', []))} entities:")
        for node in result.get("nodes", []):
            print(f"      - {node['name']} ({node.get('labels', [])})")
        print(f"   Extracted {len(result.get('edges', []))} relationships:")
        for edge in result.get("edges", []):
            print(f"      - {edge['name']}: {edge['fact'][:80]}...")

        # Search
        print("\n4. Testing search...")
        search_result = await service.search("Dionysus AI consciousness")
        print(f"   Found {len(search_result.get('nodes', []))} nodes")
        print(f"   Found {len(search_result.get('edges', []))} edges")
        for node in search_result.get("nodes", [])[:3]:
            print(f"      - {node['name']}")

        # Cleanup
        print("\n5. Closing connection...")
        await service.close()
        print("   ✓ Closed")

        print("\n" + "=" * 60)
        print("✓ All tests passed!")
        print("=" * 60)

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
