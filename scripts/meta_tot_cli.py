#!/usr/bin/env python3
"""
Meta-ToT CLI
Executes the Deterministic Meta-ToT Engine on a given problem.

Usage:
  python scripts/meta_tot_cli.py "Should I launch Feature X?"
  python scripts/meta_tot_cli.py "Problem statement" --depth 3 --branches 2
"""

import asyncio
import logging
import sys
import os
import argparse
import json
from typing import List

# Ensure we can import from api
sys.path.append(os.getcwd())

from api.services.meta_tot_engine import get_meta_tot_engine, MetaToTConfig
from api.services.worldview_integration import get_worldview_integration_service

# Configure logging to suppress debug noise, show only info/warning
logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger("dionysus.cli")

def print_box(text: str, title: str = ""):
    width = 80
    if title:
        print(f"┌─ {title} " + "─" * (width - len(title) - 4) + "┐")
    else:
        print("┌" + "─" * (width - 2) + "┐")
    
    for line in text.splitlines():
        # Simple wrapping
        while len(line) > width - 4:
            print(f"│ {line[:width-4]} │")
            line = line[width-4:]
        print(f"│ {line:<{width-4}} │")
        
    print("└" + "─" * (width - 2) + "┘")

async def run_cli(problem: str, depth: int, branches: int, verbose: bool):
    print(f"\n🧠 META-TOT CLI ACTIVATED")
    print(f"   Target: {problem}")
    print(f"   Config: Depth={depth}, Branching={branches}, Mode=Deterministic\n")
    
    engine = get_meta_tot_engine()
    
    # 1. Load System Worldview (The "Loyalty" Check)
    print("... Accessing Worldview (ActiveInferenceState Alignment) ...")
    try:
        wv_service = get_worldview_integration_service()
        # Fetch distilled wisdom related to the problem
        priors = await wv_service.get_distilled_priors(problem, limit=5)
        beliefs = {p['summary']: p['richness'] for p in priors}
        if not beliefs:
             print("   (No specific priors found. Using core axioms.)")
             beliefs = {
                 "prioritize_long_term_sovereignty": 1.0,
                 "minimize_entropy": 1.0, 
                 "favor_ antifragility": 1.0
             }
        else:
            print(f"   Loaded {len(beliefs)} Beliefs from Graph.")
    except Exception as e:
        print(f"   ⚠️ Could not load Worldview ({e}). Using fail-safe defaults.")
        beliefs = {"prioritize_long_term_sovereignty": 1.0}

    # 2. Build Context
    context = {
        "constraints": ["maximize utility", "minimize risk", "ensure alignment"],
        "user_intent": "strategic decision making",
        "beliefs": beliefs, # <--- The Magic Sauce
        "worldview_active": True
    }
    
    config = MetaToTConfig(
        max_depth=depth,
        branching_factor=branches,
        use_llm=True, # Use LLM for generation
        persist_trace=False # Don't clutter DB for CLI runs unless requested
    )
    
    print("... Reasoning (Minimizing Free Energy) ...")
    start_time = asyncio.get_running_loop().time()
    
    try:
        result, trace = await engine.run(problem, context, config_overrides=config.__dict__)
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        return

    duration = asyncio.get_running_loop().time() - start_time
    
    # Extract Best Path thoughts
    path_thoughts = []
    path_scores = []
    
    for node_id in result.best_path:
        # Find node in trace
        node = next((n for n in trace.nodes if n.node_id == node_id), None)
        if node:
            # Skip root if it's just the problem statement repeating
            if node.node_type == "root":
                continue 
            path_thoughts.append(node.thought)
            path_scores.append(node.score)

    print(f"\n✨ COMPLETE in {duration:.2f}s\n")
    
    print_box("\n".join(path_thoughts), title="WINNING PATH (Lowest Entropy)")
    
    print(f"\n📊 METRICS:")
    print(f"   Confidence: {result.confidence:.4f}")
    if path_scores:
        print(f"   Final Score: {path_scores[-1]:.4f}")
    print(f"   Total Free Energy: {result.metrics.get('total_free_energy', 0):.4f}")
    
    if verbose:
        print("\n🔍 FULL TRACE:")
        for node in trace.nodes:
            indent = "  " * node.depth
            print(f"{indent}[{node.node_type}] {node.thought[:60]}... (S={node.score:.2f})")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Meta-ToT: Deterministic Execution")
    parser.add_argument("problem", type=str, help=" The problem or question to analyze")
    parser.add_argument("--depth", type=int, default=3, help="Reasoning depth")
    parser.add_argument("--branches", type=int, default=3, help="Branching factor")
    parser.add_argument("--verbose", action="store_true", help="Show full reasoning tree")
    
    args = parser.parse_args()
    
    asyncio.run(run_cli(args.problem, args.depth, args.branches, args.verbose))
