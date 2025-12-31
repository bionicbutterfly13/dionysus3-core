"""
Belief State Models for Metacognitive Particles.

Feature: 040-metacognitive-particles
Implements probability distribution parameterized by sufficient statistics.

Key concepts:
- BeliefState: Probability distribution with mean and precision
- Precision: Inverse covariance = confidence weighting
- Entropy: Uncertainty measure computed from precision matrix

Precision bounds ensure numerical stability:
- MIN_PRECISION = 0.01 (very uncertain, open to all information)
- MAX_PRECISION = 100.0 (very certain, laser focus)

AUTHOR: Mani Saint-Victor, MD
"""

from __future__ import annotations

import logging
import math
from datetime import datetime
from typing import List, Optional
from uuid import uuid4

import numpy as np
from pydantic import BaseModel, Field, field_validator, model_validator

logger = logging.getLogger("dionysus.belief_state")

# ---------------------------------------------------------------------------
# Precision Bounds (Feature 040 - T008)
# ---------------------------------------------------------------------------

MIN_PRECISION = 0.01  # Very low confidence, open to all information
MAX_PRECISION = 100.0  # Very high confidence, laser focus


def clamp_precision(precision: float) -> float:
    """
    Clamp precision value to valid bounds.

    Args:
        precision: Raw precision value

    Returns:
        Precision clamped to [MIN_PRECISION, MAX_PRECISION]
    """
    return max(MIN_PRECISION, min(MAX_PRECISION, precision))


def clamp_precision_matrix(matrix: np.ndarray) -> np.ndarray:
    """
    Clamp all elements of a precision matrix to valid bounds.

    Args:
        matrix: Precision matrix (numpy array)

    Returns:
        Matrix with all elements clamped to [MIN_PRECISION, MAX_PRECISION]
    """
    return np.clip(matrix, MIN_PRECISION, MAX_PRECISION)


# ---------------------------------------------------------------------------
# Belief State Model (Feature 040 - T007)
# ---------------------------------------------------------------------------


class BeliefState(BaseModel):
    """
    Probability distribution parameterized by sufficient statistics.

    Represents an agent's beliefs as a Gaussian distribution with:
    - mean: Expected value of the belief
    - precision: Inverse covariance (confidence weighting)
    - entropy: Computed uncertainty measure

    The precision matrix is stored as a nested list for JSON compatibility
    but can be converted to numpy array for computation.

    Validation Rules:
    - Precision matrix must be symmetric positive-definite
    - Precision values bounded to [0.01, 100.0]
    - Entropy >= 0
    - Dimension must match mean length and precision matrix size
    """

    id: str = Field(default_factory=lambda: str(uuid4()))
    mean: List[float] = Field(
        ...,
        description="Distribution mean vector"
    )
    precision: List[List[float]] = Field(
        ...,
        description="Precision matrix (inverse covariance)"
    )
    dimension: int = Field(
        default=0,
        ge=0,
        description="Dimensionality of the belief space"
    )
    particle_id: Optional[str] = Field(
        default=None,
        description="Owning particle reference"
    )
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = {
        "json_schema_extra": {
            "example": {
                "id": "belief-001",
                "mean": [0.5, 0.5],
                "precision": [[1.0, 0.0], [0.0, 1.0]],
                "dimension": 2
            }
        }
    }

    @model_validator(mode="after")
    def validate_dimensions(self) -> "BeliefState":
        """Ensure dimensions are consistent."""
        mean_len = len(self.mean)
        precision_rows = len(self.precision)

        if precision_rows > 0:
            precision_cols = len(self.precision[0])
            if precision_rows != precision_cols:
                raise ValueError(
                    f"Precision matrix must be square, got {precision_rows}x{precision_cols}"
                )
            if mean_len != precision_rows:
                raise ValueError(
                    f"Mean length ({mean_len}) must match precision matrix size ({precision_rows})"
                )

        # Set dimension if not provided
        if self.dimension == 0:
            object.__setattr__(self, 'dimension', mean_len)
        elif self.dimension != mean_len:
            raise ValueError(
                f"Dimension ({self.dimension}) must match mean length ({mean_len})"
            )

        return self

    @field_validator("precision")
    @classmethod
    def validate_precision_bounds(cls, v: List[List[float]]) -> List[List[float]]:
        """Clamp precision values to valid bounds."""
        return [
            [clamp_precision(elem) for elem in row]
            for row in v
        ]

    @property
    def precision_array(self) -> np.ndarray:
        """Get precision as numpy array."""
        return np.array(self.precision)

    @property
    def mean_array(self) -> np.ndarray:
        """Get mean as numpy array."""
        return np.array(self.mean)

    @property
    def covariance(self) -> np.ndarray:
        """Compute covariance matrix (inverse of precision)."""
        try:
            return np.linalg.inv(self.precision_array)
        except np.linalg.LinAlgError:
            logger.warning("Precision matrix is singular, using pseudoinverse")
            return np.linalg.pinv(self.precision_array)

    @property
    def entropy(self) -> float:
        """
        Compute Gaussian entropy from precision matrix.

        Formula: H = 0.5 * d * (1 + log(2π)) - 0.5 * log(det(Π))

        Where d is dimensionality and Π is precision matrix.
        """
        d = self.dimension
        if d == 0:
            return 0.0

        try:
            det = np.linalg.det(self.precision_array)
            if det <= 0:
                logger.warning("Non-positive determinant in precision matrix")
                return float('inf')

            return 0.5 * d * (1 + math.log(2 * math.pi)) - 0.5 * math.log(det)
        except (ValueError, FloatingPointError) as e:
            logger.error(f"Error computing entropy: {e}")
            return float('inf')

    def uncertainty_reduction(self, prior: "BeliefState") -> float:
        """
        Compute uncertainty reduction from prior to this (posterior) belief.

        Returns:
            Fractional reduction in entropy: (H_prior - H_posterior) / H_prior
        """
        prior_entropy = prior.entropy
        posterior_entropy = self.entropy

        if prior_entropy <= 0 or prior_entropy == float('inf'):
            return 0.0

        return (prior_entropy - posterior_entropy) / prior_entropy

    def to_neo4j_properties(self) -> dict:
        """Convert to Neo4j node properties."""
        return {
            "id": self.id,
            "mean": self.mean,
            "precision": str(self.precision),  # Store as string for Neo4j
            "entropy": self.entropy,
            "dimension": self.dimension,
            "particle_id": self.particle_id,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

    @classmethod
    def from_mean_and_variance(
        cls,
        mean: List[float],
        variance: List[float],
        particle_id: Optional[str] = None
    ) -> "BeliefState":
        """
        Create BeliefState from mean and diagonal variance.

        Args:
            mean: Mean vector
            variance: Diagonal variance values
            particle_id: Optional owning particle

        Returns:
            BeliefState with diagonal precision matrix
        """
        d = len(mean)
        precision = [
            [clamp_precision(1.0 / v) if i == j else 0.0 for j in range(d)]
            for i, v in enumerate(variance)
        ]
        return cls(
            mean=mean,
            precision=precision,
            dimension=d,
            particle_id=particle_id
        )

    @classmethod
    def uniform_prior(cls, dimension: int, precision: float = 0.1) -> "BeliefState":
        """
        Create a uniform (low precision) prior belief state.

        Args:
            dimension: Dimensionality of the belief space
            precision: Low precision value (default 0.1)

        Returns:
            BeliefState with uniform mean and low precision
        """
        mean = [0.5] * dimension
        prec_val = clamp_precision(precision)
        prec_matrix = [
            [prec_val if i == j else 0.0 for j in range(dimension)]
            for i in range(dimension)
        ]
        return cls(mean=mean, precision=prec_matrix, dimension=dimension)


# ---------------------------------------------------------------------------
# Belief State Input for API
# ---------------------------------------------------------------------------


class BeliefStateInput(BaseModel):
    """
    Input model for API endpoints that accept belief states.

    Simplified version without auto-generated fields.
    """
    mean: List[float] = Field(..., description="Distribution mean vector")
    precision: List[List[float]] = Field(..., description="Precision matrix")
    entropy: Optional[float] = Field(
        default=None,
        description="Optional pre-computed entropy"
    )

    def to_belief_state(self, particle_id: Optional[str] = None) -> BeliefState:
        """Convert to full BeliefState model."""
        return BeliefState(
            mean=self.mean,
            precision=self.precision,
            particle_id=particle_id
        )
