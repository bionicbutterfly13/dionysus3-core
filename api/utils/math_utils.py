"""
Math utilities for network state operations.

Part of 034-network-self-modeling feature.
"""

from __future__ import annotations

import math
from typing import Union


def sigmoid_squash(value: float, min_val: float = 0.01, max_val: float = 0.99) -> float:
    """Apply sigmoid squashing to keep value in (min_val, max_val) range.

    Uses a scaled sigmoid function to smoothly constrain values without
    hard clipping, preventing exact 0 (connection death) or 1 (saturation).

    Args:
        value: Input value to squash
        min_val: Minimum output value (default: 0.01)
        max_val: Maximum output value (default: 0.99)

    Returns:
        Value constrained to (min_val, max_val) range
    """
    # Scale input to reasonable sigmoid range
    # Clamp extreme values to prevent overflow
    clamped = max(-10, min(10, value))

    # Apply sigmoid: 1 / (1 + e^(-x))
    sigmoid = 1 / (1 + math.exp(-clamped))

    # Scale to target range
    return min_val + sigmoid * (max_val - min_val)


def weight_bounds_enforcer(
    weight: float,
    min_weight: float = 0.01,
    max_weight: float = 0.99
) -> float:
    """Enforce weight boundaries using sigmoid squashing (T005).

    Keeps connection weights in (0.01, 0.99) range to prevent:
    - Connection death (weight = 0)
    - Saturation (weight = 1)

    Uses smooth sigmoid rather than hard clipping for gradient-friendly behavior.

    Args:
        weight: Raw weight value
        min_weight: Minimum allowed weight (default: 0.01)
        max_weight: Maximum allowed weight (default: 0.99)

    Returns:
        Weight constrained to (min_weight, max_weight) range
    """
    # If already in bounds, return as-is for efficiency
    if min_weight <= weight <= max_weight:
        return weight

    # Otherwise apply sigmoid squashing
    return sigmoid_squash(weight, min_weight, max_weight)


def hebbian_update(
    v1: float,
    v2: float,
    w: float,
    mu: float = 0.9
) -> float:
    """Hebbian weight update with persistence parameter.

    Implements Treur's Hebbian formula:
    hebbμ(V1, V2, W) = V1·V2·(1-W) + μ·W

    Where:
    - V1, V2: Co-activation values (0-1 normalized)
    - W: Current weight
    - μ: Persistence parameter (0-1), controls how much learned weight persists

    Args:
        v1: First activation value (0-1)
        v2: Second activation value (0-1)
        w: Current connection weight
        mu: Persistence parameter (default: 0.9)

    Returns:
        Updated weight value
    """
    return v1 * v2 * (1 - w) + mu * w


def weight_decay(
    weight: float,
    decay_rate: float,
    time_since_activation: float
) -> float:
    """Apply exponential decay to connection weight.

    Implements time-based decay for inactive connections:
    W_new = W_old * e^(-decay_rate * time)

    Args:
        weight: Current weight value
        decay_rate: Decay rate (typically 0.01)
        time_since_activation: Time in days since last activation

    Returns:
        Decayed weight value
    """
    decayed = weight * math.exp(-decay_rate * time_since_activation)
    # Enforce minimum bound
    return max(0.01, decayed)


def treur_state_update(
    current: float,
    target: float,
    speed: float,
    dt: float = 1.0
) -> float:
    """Treur temporal-causal state update.

    Implements the discrete-time difference equation:
    Y(t+Δt) = Y(t) + η[c(t) - Y(t)]Δt

    Where:
    - Y(t): Current state value
    - c(t): Target/combination function value
    - η: Speed factor (H state)
    - Δt: Time step

    Args:
        current: Current state value Y(t)
        target: Target value from combination function c(t)
        speed: Speed factor η (H state)
        dt: Time step Δt (default: 1.0)

    Returns:
        Updated state value Y(t+Δt)
    """
    return current + speed * (target - current) * dt
