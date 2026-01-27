#!/usr/bin/env python3
"""
Test ActiveInference.jl Integration

Verifies Julia-Python integration works correctly.

NOTE: This is a standalone verification script, NOT a pytest test module.
Run directly: python scripts/verification/test_active_inference_integration.py
Pytest collection is skipped via the module-level pytestmark.

Usage:
    python scripts/verification/test_active_inference_integration.py

Author: Mani Saint-Victor, MD
Date: 2026-01-03
"""

import sys
import numpy as np
from pathlib import Path

# Skip pytest collection - this is a Julia-dependent verification script
import pytest
pytestmark = pytest.mark.skip(reason="Julia-dependent verification script - run directly")

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from api.services.active_inference_service import (
    get_active_inference_service,
    GenerativeModel,
)
from api.models.belief_state import BeliefState

def test_julia_loading():
    """Test 1: Verify Julia loads successfully."""
    print("\n=== Test 1: Julia Loading ===")

    try:
        service = get_active_inference_service(lazy_load=False)
        print("✅ Julia loaded successfully")
        print("✅ ActiveInference.jl package available")
        return True
    except Exception as e:
        print(f"❌ Julia loading failed: {e}")
        return False


def test_generative_model_creation():
    """Test 2: Create a simple generative model."""
    print("\n=== Test 2: Generative Model Creation ===")

    try:
        service = get_active_inference_service()

        # Create simple 2-state, 2-observation, 2-action model
        model = service.create_simple_model(
            num_states=2,
            num_observations=2,
            num_actions=2
        )

        print(f"✅ Created generative model:")
        print(f"  - A matrix shape: {model.A.shape}")
        print(f"  - B matrix shape: {model.B.shape}")
        print(f"  - C matrix shape: {model.C.shape}")
        print(f"  - D matrix shape: {model.D.shape}")

        return True
    except Exception as e:
        print(f"❌ Model creation failed: {e}")
        return False


def test_vfe_calculation():
    """Test 3: Calculate Variational Free Energy."""
    print("\n=== Test 3: VFE Calculation ===")

    try:
        service = get_active_inference_service()

        # Create model
        model = service.create_simple_model(
            num_states=2,
            num_observations=2,
            num_actions=2
        )

        # Create belief state (uniform): mean = state probs, precision = identity
        belief = BeliefState(mean=[0.5, 0.5], precision=[[1.0, 0.0], [0.0, 1.0]])

        # Observe outcome 0
        observation = 0

        # Calculate VFE
        vfe = service.calculate_vfe(belief, observation, model)

        print(f"✅ VFE calculated: {vfe:.4f}")
        print(f"  - Belief entropy: {belief.entropy:.4f}")

        return True
    except Exception as e:
        print(f"❌ VFE calculation failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_efe_calculation():
    """Test 4: Calculate Expected Free Energy."""
    print("\n=== Test 4: EFE Calculation ===")

    try:
        service = get_active_inference_service()

        # Create model with preferences
        model = service.create_simple_model(
            num_states=2,
            num_observations=2,
            num_actions=2
        )

        # Set preference for observation 0
        model.C = np.array([[0.9], [0.1]])

        # Create belief state
        belief = BeliefState(mean=[0.6, 0.4], precision=[[1.0, 0.0], [0.0, 1.0]])

        # Policy: [action 0, action 1, action 0]
        policy = np.array([0, 1, 0])

        # Calculate EFE
        efe = service.calculate_efe(belief, model, policy, horizon=3)

        print(f"✅ EFE calculated: {efe:.4f}")
        print(f"  - Policy: {policy}")
        print(f"  - Horizon: 3 timesteps")

        return True
    except Exception as e:
        print(f"❌ EFE calculation failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_thoughtseed_selection():
    """Test 5: ThoughtSeed selection via VFE minimization."""
    print("\n=== Test 5: ThoughtSeed Selection ===")

    try:
        service = get_active_inference_service()

        # Create mock thoughtseeds
        model1 = service.create_simple_model(2, 2, 2)
        model2 = service.create_simple_model(2, 2, 2)

        thoughtseeds = [
            {
                'id': 'ts1',
                'activation_level': 0.7,
                'belief_state': BeliefState(qs=np.array([0.8, 0.2])),
                'observation': 0,
                'generative_model': model1
            },
            {
                'id': 'ts2',
                'activation_level': 0.6,
                'belief_state': BeliefState(qs=np.array([0.5, 0.5])),
                'observation': 1,
                'generative_model': model2
            },
            {
                'id': 'ts3',
                'activation_level': 0.4,  # Below threshold
                'belief_state': BeliefState(qs=np.array([0.3, 0.7])),
                'observation': 0,
                'generative_model': model1
            }
        ]

        # Select dominant
        dominant = service.select_dominant_thoughtseed(
            thoughtseeds,
            threshold=0.5
        )

        if dominant:
            print(f"✅ Dominant ThoughtSeed selected: {dominant['id']}")
            print(f"  - Activation level: {dominant['activation_level']:.2f}")
            print(f"  - Active pool size: 2/3 (threshold=0.5)")
        else:
            print("❌ No dominant ThoughtSeed (pool was empty)")
            return False

        return True
    except Exception as e:
        print(f"❌ ThoughtSeed selection failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    print("="*60)
    print("ACTIVE INFERENCE INTEGRATION TEST SUITE")
    print("="*60)

    tests = [
        ("Julia Loading", test_julia_loading),
        ("Generative Model", test_generative_model_creation),
        ("VFE Calculation", test_vfe_calculation),
        ("EFE Calculation", test_efe_calculation),
        ("ThoughtSeed Selection", test_thoughtseed_selection)
    ]

    results = []
    for name, test_func in tests:
        try:
            passed = test_func()
            results.append((name, passed))
        except Exception as e:
            print(f"\n❌ Test '{name}' crashed: {e}")
            import traceback
            traceback.print_exc()
            results.append((name, False))

    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)

    passed_count = sum(1 for _, passed in results if passed)
    total_count = len(results)

    for name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {name}")

    print("-"*60)
    print(f"Total: {passed_count}/{total_count} tests passed")
    print("="*60)

    return 0 if passed_count == total_count else 1


if __name__ == "__main__":
    exit(main())
