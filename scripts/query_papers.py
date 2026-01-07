#!/usr/bin/env python3
"""
RAG Query Interface for Academic Papers

Semantic search across ingested papers with vector similarity.

Usage:
    # Semantic search
    python scripts/query_papers.py "What is the EFE decomposition?"

    # Search with filters
    python scripts/query_papers.py "POMDP formulation" --year 2025 --author Nehrer

    # Find equations by concept
    python scripts/query_papers.py --concept VFE --mode equation

    # Cross-reference concept across papers
    python scripts/query_papers.py --concept "Expected Free Energy" --mode cross-reference

Author: Mani Saint-Victor, MD
Date: 2026-01-03
"""

import asyncio
import logging
import os
import argparse
from typing import List, Dict, Optional
import json

# Embeddings
from litellm import aembedding
import numpy as np

# HTTP for n8n webhooks
import requests

# Graphiti for dev queries
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PaperRAG:
    """RAG interface for academic paper knowledge base."""

    def __init__(self, use_production: bool = False):
        self.use_production = use_production
        self.n8n_base = "https://72.61.78.89:5678"
        self.embedding_model = "text-embedding-3-small"

    async def search(
        self,
        query: str,
        top_k: int = 5,
        filters: Optional[Dict] = None
    ) -> List[Dict]:
        """
        Semantic search across paper chunks.

        Args:
            query: Natural language query
            top_k: Number of results to return
            filters: Optional filters (year, author, journal)

        Returns:
            [
                {
                    "chunk_id": "...",
                    "text": "...",
                    "similarity": 0.87,
                    "metadata": {
                        "paper": "...",
                        "section": "...",
                        "page_range": [3, 5]
                    }
                },
                ...
            ]
        """
        logger.info(f"Searching: '{query}' (top_k={top_k})")

        # Generate query embedding
        query_embedding = await self._embed_query(query)

        # Search
        if self.use_production:
            results = await self._search_via_n8n(query_embedding, top_k, filters)
        else:
            results = await self._search_via_graphiti(query, top_k)

        logger.info(f"Found {len(results)} results")
        return results

    async def find_equation(
        self,
        concept: str,
        paper_filter: Optional[str] = None
    ) -> List[Dict]:
        """
        Find equations implementing a concept.

        Args:
            concept: Concept name (e.g., "VFE", "EFE", "POMDP")
            paper_filter: Optional paper title/author filter

        Returns:
            [
                {
                    "equation": "F = D_{KL}[q(s) || p(o,s)]",
                    "number": "Eq 5",
                    "paper": "Nehrer et al. (2025)",
                    "context": "...",
                    "page": 4
                },
                ...
            ]
        """
        logger.info(f"Finding equations for concept: {concept}")

        if self.use_production:
            payload = {
                "concept": concept,
                "paper_filter": paper_filter
            }

            response = requests.post(
                f"{self.n8n_base}/webhook/papers/find-equation",
                json=payload,
                verify=False
            )
            response.raise_for_status()
            equations = response.json()["equations"]

        else:
            # Graphiti path - search for concept mentions
            equations = await self._find_equations_graphiti(concept, paper_filter)

        logger.info(f"Found {len(equations)} equations")
        return equations

    async def cross_reference(
        self,
        concept: str
    ) -> List[Dict]:
        """
        Find how different papers implement the same concept.

        Returns:
            [
                {
                    "concept": "VFE",
                    "paper": "Kavi et al. (2025)",
                    "equation": "Eq 3",
                    "latex": "F_i = D_KL[...]",
                    "context": "..."
                },
                ...
            ]
        """
        logger.info(f"Cross-referencing concept: {concept}")

        if self.use_production:
            payload = {"concept": concept}

            response = requests.post(
                f"{self.n8n_base}/webhook/papers/cross-reference",
                json=payload,
                verify=False
            )
            response.raise_for_status()
            results = response.json()["implementations"]

        else:
            # Graphiti path - search across groups
            results = await self._cross_reference_graphiti(concept)

        logger.info(f"Found {len(results)} implementations")
        return results

    # ========================================================================
    # Internal Methods
    # ========================================================================

    async def _embed_query(self, query: str) -> np.ndarray:
        """Generate embedding for query."""
        response = await aembedding(
            model=self.embedding_model,
            input=[query]
        )
        return np.array(response.data[0]["embedding"])

    async def _search_via_n8n(
        self,
        query_embedding: np.ndarray,
        top_k: int,
        filters: Optional[Dict]
    ) -> List[Dict]:
        """Search via n8n webhook (production)."""
        payload = {
            "query_embedding": query_embedding.tolist(),
            "top_k": top_k,
            "filters": filters or {}
        }

        response = requests.post(
            f"{self.n8n_base}/webhook/papers/search-similar",
            json=payload,
            verify=False
        )
        response.raise_for_status()

        return response.json()["results"]

    async def _search_via_graphiti(
        self,
        query: str,
        top_k: int
    ) -> List[Dict]:
        """Search via Graphiti (development)."""
        from api.services.graphiti_service import get_graphiti_service

        service = await get_graphiti_service()

        # Search across all paper groups
        # Note: Graphiti doesn't support vector similarity natively yet
        # This is a text-based search fallback

        results = await service.search(
            query=query,
            limit=top_k
        )

        # Format results
        formatted = []
        for edge in results.get("edges", []):
            formatted.append({
                "text": edge.get("fact", ""),
                "similarity": edge.get("search_score", 0.0),
                "metadata": {
                    "source": edge.get("source_description", ""),
                    "group_id": edge.get("group_id", "")
                }
            })

        return formatted

    async def _find_equations_graphiti(
        self,
        concept: str,
        paper_filter: Optional[str]
    ) -> List[Dict]:
        """Find equations via Graphiti (development)."""
        from api.services.graphiti_service import get_graphiti_service

        service = await get_graphiti_service()

        # Search for concept + "equation" mentions
        query = f"{concept} equation"
        results = await service.search(query=query, limit=20)

        # Filter and format
        equations = []
        for edge in results.get("edges", []):
            fact = edge.get("fact", "")
            if "Eq " in fact or "Equation" in fact:
                equations.append({
                    "equation": "[LaTeX from PDF extraction]",
                    "number": "Unknown",
                    "paper": edge.get("source_description", ""),
                    "context": fact,
                    "page": 0
                })

        return equations

    async def _cross_reference_graphiti(self, concept: str) -> List[Dict]:
        """Cross-reference via Graphiti (development)."""
        # Search across all paper groups for concept
        from api.services.graphiti_service import get_graphiti_service

        service = await get_graphiti_service()

        results = await service.search(query=concept, limit=50)

        # Group by source (paper)
        by_paper = {}
        for edge in results.get("edges", []):
            source = edge.get("source_description", "Unknown")
            if source not in by_paper:
                by_paper[source] = []
            by_paper[source].append({
                "concept": concept,
                "paper": source,
                "context": edge.get("fact", "")
            })

        # Flatten
        implementations = []
        for paper, mentions in by_paper.items():
            implementations.extend(mentions)

        return implementations


# ============================================================================
# CLI Interface
# ============================================================================

def format_results(results: List[Dict], mode: str) -> str:
    """Format results for display."""
    if mode == "search":
        output = "\n" + "="*80 + "\n"
        output += "SEARCH RESULTS\n"
        output += "="*80 + "\n\n"

        for i, result in enumerate(results, 1):
            output += f"[{i}] Similarity: {result.get('similarity', 0.0):.3f}\n"
            output += f"Section: {result.get('metadata', {}).get('section', 'Unknown')}\n"
            output += f"Paper: {result.get('metadata', {}).get('paper', 'Unknown')}\n"
            output += f"Pages: {result.get('metadata', {}).get('page_range', [])}\n"
            output += f"\n{result.get('text', '')[:500]}...\n"
            output += "-"*80 + "\n\n"

        return output

    elif mode == "equation":
        output = "\n" + "="*80 + "\n"
        output += "EQUATION SEARCH RESULTS\n"
        output += "="*80 + "\n\n"

        for i, eq in enumerate(results, 1):
            output += f"[{i}] {eq.get('number', 'Unknown')} (Page {eq.get('page', 'N/A')})\n"
            output += f"Paper: {eq.get('paper', 'Unknown')}\n"
            output += f"LaTeX: {eq.get('equation', '[Not extracted]')}\n"
            output += f"Context: {eq.get('context', '')[:200]}...\n"
            output += "-"*80 + "\n\n"

        return output

    elif mode == "cross-reference":
        output = "\n" + "="*80 + "\n"
        output += "CROSS-REFERENCE RESULTS\n"
        output += "="*80 + "\n\n"

        # Group by paper
        by_paper = {}
        for impl in results:
            paper = impl.get('paper', 'Unknown')
            if paper not in by_paper:
                by_paper[paper] = []
            by_paper[paper].append(impl)

        for paper, impls in by_paper.items():
            output += f"Paper: {paper}\n"
            output += f"Concept: {impls[0].get('concept', 'Unknown')}\n"
            for impl in impls:
                if impl.get('equation'):
                    output += f"  {impl.get('equation', '')}\n"
                if impl.get('context'):
                    output += f"  Context: {impl.get('context', '')[:150]}...\n"
            output += "-"*80 + "\n\n"

        return output

    return ""


async def main_async(args):
    """Async main function."""
    rag = PaperRAG(use_production=args.production)

    # Build filters
    filters = {}
    if args.year:
        filters["year"] = args.year
    if args.author:
        filters["author"] = args.author

    # Execute query based on mode
    if args.mode == "search":
        if not args.query:
            print("Error: --query required for search mode")
            return 1

        results = await rag.search(
            query=args.query,
            top_k=args.top_k,
            filters=filters
        )

        print(format_results(results, mode="search"))

    elif args.mode == "equation":
        if not args.concept:
            print("Error: --concept required for equation mode")
            return 1

        results = await rag.find_equation(
            concept=args.concept,
            paper_filter=args.author
        )

        print(format_results(results, mode="equation"))

    elif args.mode == "cross-reference":
        if not args.concept:
            print("Error: --concept required for cross-reference mode")
            return 1

        results = await rag.cross_reference(concept=args.concept)

        print(format_results(results, mode="cross-reference"))

    # Save results to JSON if requested
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(results, f, indent=2)
        logger.info(f"Results saved to {args.output}")

    return 0


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Query academic papers via RAG"
    )
    parser.add_argument(
        "query",
        nargs="?",
        type=str,
        help="Search query (natural language)"
    )
    parser.add_argument(
        "--mode",
        choices=["search", "equation", "cross-reference"],
        default="search",
        help="Query mode (default: search)"
    )
    parser.add_argument(
        "--concept",
        type=str,
        help="Concept name for equation/cross-reference mode (e.g., 'VFE', 'EFE')"
    )
    parser.add_argument(
        "--top-k",
        type=int,
        default=5,
        help="Number of results to return (default: 5)"
    )
    parser.add_argument(
        "--year",
        type=int,
        help="Filter by publication year"
    )
    parser.add_argument(
        "--author",
        type=str,
        help="Filter by author name"
    )
    parser.add_argument(
        "--production",
        action="store_true",
        help="Use n8n webhooks (production) instead of Graphiti (dev)"
    )
    parser.add_argument(
        "--output",
        type=str,
        help="Save results to JSON file"
    )

    args = parser.parse_args()

    try:
        exit_code = asyncio.run(main_async(args))
        return exit_code
    except Exception as e:
        logger.error(f"Query failed: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    exit(main())
