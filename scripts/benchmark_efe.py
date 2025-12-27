import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import time
import numpy as np
from api.services.efe_engine import EFEEngine

def run_benchmark():
    engine = EFEEngine()
    goal_vector = np.random.rand(768).tolist()
    
    seeds = []
    for i in range(100):
        seeds.append({
            "id": f"seed_{i}",
            "response_vector": np.random.rand(768).tolist(),
            "prediction_probabilities": [0.7, 0.3]
        })
        
    start = time.time()
    response = engine.calculate_efe("benchmark query", goal_vector, seeds)
    end = time.time()
    
    total_ms = (end - start) * 1000
    per_seed_ms = total_ms / 100
    
    print(f"EFE Benchmark:")
    print(f"  Total time for 100 seeds: {total_ms:.2f}ms")
    print(f"  Average time per seed: {per_seed_ms:.2f}ms")
    
    if per_seed_ms < 50:
        print("✓ NFR-030-001 Compliant (<50ms)")
    else:
        print("✗ NFR-030-001 Violated (>50ms)")

if __name__ == "__main__":
    run_benchmark()
