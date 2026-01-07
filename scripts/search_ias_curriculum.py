#!/usr/bin/env python3
"""
Search Graphiti knowledge graph for Inner Architect System curriculum structure.
Uses approved Graphiti service (not direct Neo4j access).
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from api.services.graphiti_service import get_graphiti_service


async def search_ias_curriculum():
    """Search for Inner Architect System curriculum in Graphiti."""
    graphiti = await get_graphiti_service()
    
    print("🔍 Searching Graphiti for Inner Architect System curriculum...\n")
    
    # Search queries to find curriculum structure
    search_queries = [
        "Inner Architect System curriculum",
        "Inner Architect phases",
        "Inner Architect lessons",
        "Analytical Empaths curriculum",
        "IAS course structure"
    ]
    
    results = {}
    
    for query in search_queries:
        print(f"Query: {query}")
        try:
            search_results = await graphiti.search(query, num_results=5)
            if search_results:
                results[query] = search_results
                print(f"  ✓ Found {len(search_results)} results")
                for idx, result in enumerate(search_results, 1):
                    print(f"    {idx}. {result.get('name', 'N/A')} - {result.get('summary', 'N/A')[:80]}")
            else:
                print(f"  ✗ No results")
        except Exception as e:
            print(f"  ✗ Error: {e}")
        print()
    
    # Try direct Cypher query for entities related to curriculum
    print("\n📊 Querying for curriculum-related entities...\n")
    
    cypher_queries = [
        """
        MATCH (e:Entity)
        WHERE e.name CONTAINS 'Inner Architect' OR e.name CONTAINS 'curriculum' OR e.name CONTAINS 'phase'
        RETURN e.name as name, e.summary as summary, labels(e) as labels
        LIMIT 20
        """,
        """
        MATCH (e:Entity)-[r]->(related:Entity)
        WHERE e.name CONTAINS 'Inner Architect' OR e.name CONTAINS 'Analytical Empath'
        RETURN e.name as entity, type(r) as relationship, related.name as related_entity
        LIMIT 20
        """
    ]
    
    for idx, query in enumerate(cypher_queries, 1):
        print(f"Cypher Query {idx}:")
        try:
            result = await graphiti.execute_cypher(query.strip())
            if result:
                print(f"  ✓ Found {len(result)} records")
                for record in result[:10]:  # Show first 10
                    print(f"    - {record}")
            else:
                print(f"  ✗ No results")
        except Exception as e:
            print(f"  ✗ Error: {e}")
        print()
    
    return results


if __name__ == "__main__":
    asyncio.run(search_ias_curriculum())
